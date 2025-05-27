// using System;
// using System.Threading.Tasks;
// using SocketIOClient;
// using System.Text.Json;
// using System.IO;
// using SocketIO.Core;

// class Program
// {
//     static async Task(string[] args)
//     {
//         var options = new SocketIOOptions
//         {
//             Transport = SocketIOClient.Transport.TransportProtocol.WebSocket,
//             Reconnection = true,
//             ReconnectionAttempts = 5,
//             ReconnectionDelay = 1000,
//             EIO = EngineIO.V4
//         };

//         var client = new SocketIOClient.SocketIO("http://localhost:5001", options);

//         client.OnConnected += async (sender, e) =>
//         {
//             Console.WriteLine("서버에 연결되었습니다.");
            
//             // Excel 파일 경로
//             string excelFilePath = Path.Combine("test_excel_file", "사람정보.xlsx");
            
//             if (!File.Exists(excelFilePath))
//             {
//                 Console.WriteLine($"Excel 파일을 찾을 수 없습니다: {excelFilePath}");
//                 return;
//             }

//             // Excel 파일을 바이트 배열로 읽기
//             byte[] excelBytes = File.ReadAllBytes(excelFilePath);
//             string base64Excel = Convert.ToBase64String(excelBytes);
            
//             // 테스트용 요청 데이터
//             var request = new
//             {
//                 command = "search_similar_context",
//                 chat_id = 1,
//                 prompt = "Excel 데이터 분석",
//                 request_type = 1, // 1: explain
//                 description = "사람 정보 데이터 분석",
//                 current_program = new
//                 {
//                     id = 1,
//                     type = "excel",
//                     context = "사람 정보"
//                 },
//                 target_program = new
//                 {
//                     id = 2,
//                     type = "word",
//                     context = "분석 보고서"
//                 },
//                 file_data = new
//                 {
//                     filename = "사람정보.xlsx",
//                     content = base64Excel,
//                     content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
//                 }
//             };

//             Console.WriteLine("요청 데이터:");
//             Console.WriteLine(JsonSerializer.Serialize(request, new JsonSerializerOptions { WriteIndented = true }));
            
//             Console.WriteLine("요청 전송 중...");
//             await client.EmitAsync("message", request);
//             Console.WriteLine("요청 전송 완료");
//         };

//         client.On("message_response", response =>
//         {
//             var result = response.GetValue<dynamic>();
//             Console.WriteLine($"응답 수신:");
//             Console.WriteLine($"Chat ID: {result.chat_id}");
//             Console.WriteLine($"Status: {result.status}");
//             Console.WriteLine($"Response: {result.response}");
//         });

//         client.OnError += (sender, e) =>
//         {
//             Console.WriteLine($"에러 발생: {e}");
//         };

//         client.OnDisconnected += (sender, e) =>
//         {
//             Console.WriteLine("서버와 연결이 끊어졌습니다.");
//         };

//         try
//         {
//             Console.WriteLine("서버 연결 시도 중...");
//             await client.ConnectAsync();
//             Console.WriteLine("서버 연결 성공");
//             Console.WriteLine("종료하려면 아무 키나 누르세요...");
//             Console.ReadKey();
//         }
//         catch (Exception ex)
//         {
//             Console.WriteLine($"연결 중 에러 발생: {ex.Message}");
//         }
//     }
// }

using System;
using System.Threading.Tasks;
using System.Threading;
using SocketIOClient;
using System.Text.Json;
using SocketIO.Core;

class Program
{
    private static TaskCompletionSource<bool> responseReceived;
    private static readonly int ResponseTimeoutSeconds = 30;

    static async Task Main(string[] args)
    {
        var options = new SocketIOOptions
        {
            Transport = SocketIOClient.Transport.TransportProtocol.WebSocket,
            Reconnection = true,
            ReconnectionAttempts = 5,
            ReconnectionDelay = 1000,
            EIO = EngineIO.V4
        };

        var client = new SocketIOClient.SocketIO("http://localhost:5001", options);
        
        try
        {
            Console.WriteLine("서버 연결 시도 중...");
            await client.ConnectAsync();
            Console.WriteLine("서버 연결 성공");

            // 요청 전송 및 응답 대기를 위한 TaskCompletionSource
            responseReceived = new TaskCompletionSource<bool>();

            // 테스트용 요청 데이터
            var request = new
            {
                command = "request_prompt",
                chat_id = 1,
                prompt = "이 파일에 적힌 내용을 모두 한글로 변환해줘",
                request_type = 1, // 1: freestyle, 2: generate_text, 3: explain, 4: summary
                current_program = new
                {
                    context = "<table style='border-collapse:collapse'><tr><td style='background-color: #FFFF00; text-align: left; vertical-align: bottom; border-top: 1px solid #000000; border-left: 1px solid #000000'>AA</td><td style='text-align: left; vertical-align: bottom; border-top: 1px solid #000000'><u>DD</u></td><td style='text-align: left; vertical-align: bottom; border-top: 1px solid #000000; border-right: 1px solid #000000'></td></tr><tr><td style='text-align: left; vertical-align: bottom; border-left: 1px solid #000000'></td><td style='color: #FF0000; text-align: left; vertical-align: bottom'>BB</td><td style='font-size: 14pt; text-align: left; vertical-align: bottom; border-right: 1px solid #000000'><i>AA</i></td></tr><tr><td style='text-align: left; vertical-align: bottom; border-bottom: 1px solid #000000; border-left: 1px solid #000000'></td><td style='text-align: left; vertical-align: bottom; border-bottom: 1px solid #000000'>GG</td><td style='text-align: left; vertical-align: bottom; border-right: 1px solid #000000; border-bottom: 1px solid #000000'></td></tr></table>",
                    fileId = 21955048185373228UL,     // ulong? (nullable) 파일 고유 아이디
                    volumeId = 2524257335U,          // uint? (nullable) 드라이브 아이디
                    fileType = "Excel",             // string
                    fileName = "test.xlsx",         // string
                    filePath = "C:\\...\\test.xlsx" // string
                },
                target_program = (object)null
            };

            // 이벤트 핸들러 설정
            client.On("message_response", response =>
            {
                try
                {
                    Console.WriteLine("\n원본 응답 데이터 타입: " + response.GetType().FullName);
                    Console.WriteLine("원본 응답 데이터:");
                    Console.WriteLine(JsonSerializer.Serialize(response, new JsonSerializerOptions { WriteIndented = true }));

                    // 응답을 JsonElement로 파싱
                    var jsonElement = response.GetValue<System.Text.Json.JsonElement>();
                    Console.WriteLine("\n파싱된 JSON 데이터:");
                    Console.WriteLine(JsonSerializer.Serialize(jsonElement, new JsonSerializerOptions { WriteIndented = true }));

                    // 필드 존재 여부 확인
                    if (jsonElement.TryGetProperty("command", out var commandElement))
                    {
                        Console.WriteLine($"Command: {commandElement.GetString()}");
                    }
                    if (jsonElement.TryGetProperty("status", out var statusElement))
                    {
                        Console.WriteLine($"Status: {statusElement.GetString()}");
                    }
                    if (jsonElement.TryGetProperty("message", out var messageElement))
                    {
                        Console.WriteLine($"Message: {messageElement.GetString()}");
                    }

                    // 응답 수신 완료 알림
                    responseReceived.TrySetResult(true);
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"\n응답 처리 중 오류 발생: {ex.GetType().FullName}");
                    Console.WriteLine($"오류 메시지: {ex.Message}");
                    Console.WriteLine($"스택 트레이스: {ex.StackTrace}");
                    if (response != null)
                    {
                        Console.WriteLine($"원본 응답: {response}");
                    }
                    // 오류 발생 시에도 응답 수신 완료 처리
                    responseReceived.TrySetException(ex);
                }
            });

            client.OnError += (sender, e) =>
            {
                Console.WriteLine($"\n에러 발생: {e}");
                responseReceived.TrySetException(new Exception($"소켓 에러: {e}"));
            };

            client.OnDisconnected += (sender, e) =>
            {
                Console.WriteLine("서버와 연결이 끊어졌습니다.");
                responseReceived.TrySetException(new Exception("서버 연결 끊김"));
            };

            // 요청 전송
            Console.WriteLine("\n요청 데이터:");
            Console.WriteLine(JsonSerializer.Serialize(request, new JsonSerializerOptions { WriteIndented = true }));
            
            Console.WriteLine("\n요청 전송 중...");
            await client.EmitAsync("message", request);
            Console.WriteLine("요청 전송 완료");

            // 응답 대기
            try
            {
                Console.WriteLine("\nFlask 서버 응답 대기 중...");
                using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(ResponseTimeoutSeconds));
                await responseReceived.Task.WaitAsync(cts.Token);
                Console.WriteLine("응답 처리 완료");

                // 새로운 요청을 위한 TaskCompletionSource 재설정
                responseReceived = new TaskCompletionSource<bool>();

                // 이전 대화를 기억하는 새로운 요청
                var followUpRequest = new
                {
                    command = "request_prompt",
                    chat_id = 1,  // chat_id를 1로 유지
                    prompt = "방금 내가 뭐라고 물어봤지?",
                    request_type = 1 // freestyle
                };

                Console.WriteLine("\n후속 요청 데이터:");
                Console.WriteLine(JsonSerializer.Serialize(followUpRequest, new JsonSerializerOptions { WriteIndented = true }));
                
                Console.WriteLine("\n후속 요청 전송 중...");
                await client.EmitAsync("message", followUpRequest);
                Console.WriteLine("후속 요청 전송 완료");

                // 후속 요청에 대한 응답 대기
                Console.WriteLine("\n후속 요청에 대한 응답 대기 중...");
                await responseReceived.Task.WaitAsync(cts.Token);
                Console.WriteLine("후속 응답 처리 완료");
            }
            catch (OperationCanceledException)
            {
                Console.WriteLine($"\n{ResponseTimeoutSeconds}초 동안 응답이 없어 타임아웃되었습니다.");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"\n응답 대기 중 오류 발생: {ex.Message}");
            }

            // 프로그램 종료 대기
            Console.WriteLine("\n종료하려면 아무 키나 누르세요...");
            Console.ReadKey();
        }
        catch (Exception ex)
        {
            Console.WriteLine($"연결 중 에러 발생: {ex.Message}");
        }
        finally
        {
            // 연결 종료
            await client.DisconnectAsync();
        }
    }
} 
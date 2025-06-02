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
                generated_timestamp = "2025-06-01T06:56:07Z", 
                chat_id = -2,
                title = "",
                prompt = "주어진 시를 모음집에 형식을 맞춰서 추가해줘. 제목과 앞의 한두 문단을 추가하면 돼.",
                request_type = 5, // convert 
                current_program = new
                {
                    context = "\u003Cspan style=\u0027font-size: 15pt; color: #000000\u0027\u003E\u003Cb\u003E\uBCC4 \uD5E4\uB294 \uBC24\u003C/b\u003E\u003C/span\u003E\u003Cbr\u003E\u003Cspan style=\u0027font-size: 15pt; color: #000000\u0027\u003E\u003Cb\u003E\u003C/b\u003E\u003C/span\u003E\u003Cspan style=\u0027font-size: 14pt; color: #000000\u0027\u003E\uC724\uB3D9\uC8FC\u003C/span\u003E\u003Cbr\u003E\u003Cspan style=\u0027font-size: 14pt; color: #000000\u0027\u003E\u003C/span\u003E\u003Cspan style=\u0027color: #000000\u0027\u003E\uACC4\uC808\uC774 \uC9C0\uB098 \uAC00\uB294 \uD558\uB298\uC5D0\uB294\u003C/span\u003E\u003Cbr\u003E\u003Cspan style=\u0027color: #000000\u0027\u003E\uAC00\uC744\uB85C \uAC00\uB4DD \uCC28 \uC788\uC2B5\uB2C8\uB2E4.\u003C/span\u003E\u003Cbr\u003E\u003Cspan style=\u0027color: #000000\u0027\u003E\u200B\u003C/span\u003E\u003Cbr\u003E\u003Cspan style=\u0027color: #000000\u0027\u003E\uB098\uB294 \uC544\uBB34 \uAC71\uC815\uB3C4 \uC5C6\uC774\u003C/span\u003E\u003Cbr\u003E\u003Cspan style=\u0027color: #000000\u0027\u003E\uAC00\uC744 \uC18D\uC758 \uBCC4\uB4E4\uC744 \uB2E4 \uD5E4\uC77C \uB4EF\uD569\uB2C8\uB2E4.\u003C/span\u003E\u003Cbr\u003E\u003Cspan style=\u0027color: #000000\u0027\u003E\u200B\u003C/span\u003E\u003Cbr\u003E\u003Cspan style=\u0027color: #000000\u0027\u003E\uAC00\uC2B4\uC18D\uC5D0 \uD558\uB098 \uB458 \uC0C8\uACA8\uC9C0\uB294 \uBCC4\uC744\u003C/span\u003E\u003Cbr\u003E\u003Cspan style=\u0027color: #000000\u0027\u003E\uC774\uC81C \uB2E4 \uBABB \uD5E4\uB294 \uAC83\uC740\u003C/span\u003E\u003Cbr\u003E\u003Cspan style=\u0027color: #000000\u0027\u003E\uC26C\uC774 \uC544\uCE68\uC774 \uC624\uB294 \uAE4C\uB2ED\uC774\uC694,\u003C/span\u003E\u003Cbr\u003E\u003Cspan style=\u0027color: #000000\u0027\u003E\uB0B4\uC77C \uBC24\uC774 \uB0A8\uC740 \uAE4C\uB2ED\uC774\uC694,\u003C/span\u003E\u003Cbr\u003E\u003Cspan style=\u0027color: #000000\u0027\u003E\uC544\uC9C1 \uB098\uC758 \uCCAD\uCD98\uC774 \uB2E4\uD558\uC9C0 \uC54A\uC740 \uAE4C\uB2ED\uC785\uB2C8\uB2E4.\u003C/span\u003E\u003Cbr\u003E\u003Cspan style=\u0027color: #000000\u0027\u003E\u200B\u003C/span\u003E\u003Cbr\u003E\u003Cspan style=\u0027color: #000000\u0027\u003E\uBCC4 \uD558\uB098\uC5D0 \uCD94\uC5B5\uACFC\u003C/span\u003E\u003Cbr\u003E\u003Cspan style=\u0027color: #000000\u0027\u003E\uBCC4 \uD558\uB098\uC5D0 \uC0AC\uB791\uACFC\u003C/span\u003E\u003Cbr\u003E\u003Cspan style=\u0027color: #000000\u0027\u003E\uBCC4 \uD558\uB098\uC5D0 \uC4F8\uC4F8\uD568\uACFC\u003C/span\u003E\u003Cbr\u003E\u003Cspan style=\u0027color: #000000\u0027\u003E\uBCC4 \uD558\uB098\uC5D0 \uB3D9\uACBD\uACFC\u003C/span\u003E\u003Cbr\u003E\u003Cspan style=\u0027color: #000000\u0027\u003E\uBCC4 \uD558\uB098\uC5D0 \uC2DC\uC640\u003C/span\u003E\u003Cbr\u003E\u003Cspan style=\u0027color: #000000\u0027\u003E\uBCC4 \uD558\uB098\uC5D0 \uC5B4\uBA38\uB2C8, \uC5B4\uBA38\uB2C8\u003C/span\u003E\u003Cbr\u003E\u003Cbr\u003E",   
                    fileId = 5629499534453704,
                    volumeId = 3163409098,
                    fileType = "Word",
                    fileName = "\uBCC4 \uD5E4\uB294 \uBC24.docx",
                    filePath = @"C:\Users\kjbdd\OneDrive\바탕 화면\test data\case 1 word - word\별 헤는 밤.docx",
                    position = "1-20",
                    generated_context = ""
                },
                target_program = new
                {
                    context = "<span style='font-size: 15pt; color: #000000'> <굴뚝>  산골짜기 오막살이 낮은 굴뚝엔몽기몽기 웨인연기 대낮에 솟나,</span><br><span style='font-size: 15pt; color: #000000'></span><span style='font-size: 14pt; color: #000000'><돌아와 보는 밤>세상으로부터 돌아오듯이 이제 내 좁은 방에 돌아와불을 끄옵니다. 불을 켜두는 것은 너무나 피로롭은일이옵니다. 그것은 낮의 연장이옵기에</span><br><br><span style='font-size: 14pt; color: #000000'><또 다른 고향> 고향에 돌아온 날 밤에 내 백골이 따라와 한방에 누웠다 </span><br><br><span style='font-size: 14pt; color: #000000'><무서운 시간>거 나를 부르는 것이 누구요,가랑잎 이파리 푸르러 나오는 그늘인데,나 아직 여기 호흡이 남아 있소.</span><br><br><span style='font-size: 14pt; color: #000000'><바다> 실어다 뿌리는 바람처럼 씨원타. </span><br><br><span style='font-size: 14pt; color: #000000'><봄> 봄이 혈관 속에 시내처럼 흘러돌, 돌, 시내 가차운 언덕에개나리, 진달래, 노-란 배추꽃,</span><br>",   
                    fileId = 25895697857580618,
                    volumeId = 3163409098,
                    fileType = "Word",
                    fileName = "\uC724\uB3D9\uC8FC \uC2DC \uBAA8\uC74C\uC9D1.docx",
                    filePath = "C:\\Users\\kjbdd\\OneDrive\\\uBC14\uD0D5 \uD654\uBA74\\test data\\case 1 word - word\\\uC724\uB3D9\uC8FC \uC2DC \uBAA8\uC74C\uC9D1.docx",
                }
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
                    prompt = "지금까지 내가 물어본게 어떤 게 있어?",
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
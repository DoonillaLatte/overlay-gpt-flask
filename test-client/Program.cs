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
                generated_timestamp = "2025-05-27T02:06:50Z",
                prompt = "AI모델 분석 내용인데 이 워드에 표에 대한 설명 적어줘.",
                request_type = 1,
                current_program = new
                {
                    context = @"<table style='border-collapse:collapse'><tr><td style='background-color: #C0CDEF; text-align: left; vertical-align: bottom; border-top: 1px solid #000000; border-right: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000'><b>제한사항 구분</b></td><td style='background-color: #C0CDEF; text-align: left; vertical-align: bottom; border-top: 1px solid #000000; border-right: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000'><b>정확도 하락 원인 분석</b></td><td style='background-color: #C0CDEF; text-align: left; vertical-align: bottom; border-top: 1px solid #000000; border-right: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000'><b>테스트케이스 비율 포함 여부</b></td></tr><tr><td style='background-color: #C0CDEF; text-align: left; vertical-align: bottom; border-top: 1px solid #000000; border-right: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000'>건물 지붕 외 설치 대상</td><td style='text-align: left; vertical-align: bottom; border-top: 1px solid #000000; border-right: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000'>건물이 존재하지 않은 사진 입력 시(로, 락 등) 인식 정확도 저하</td><td style='text-align: left; vertical-align: bottom; border-top: 1px solid #000000; border-right: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000'>O</td></tr><tr><td style='background-color: #C0CDEF; text-align: left; vertical-align: bottom; border-top: 1px solid #000000; border-right: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000'>지붕 설치 제한사항</td><td style='text-align: left; vertical-align: bottom; border-top: 1px solid #000000; border-right: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000'>지붕의 형태에 따라 계산되는 면적이 다름
추후 모델 추가 학습 or 분류 모델 도입으로 해결해야 함</td><td style='text-align: left; vertical-align: bottom; border-top: 1px solid #000000; border-right: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000'>O</td></tr><tr><td style='background-color: #C0CDEF; text-align: left; vertical-align: bottom; border-top: 1px solid #000000; border-right: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000'>다중 건물 설치</td><td style='text-align: left; vertical-align: bottom; border-top: 1px solid #000000; border-right: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000'>여러 건물에 걸쳐 계산된 발전량인 경우와 단일 건물만 계산된 발전량인 경우를 구분하기 위한 지표 X
주변 건물 발전량 계산 누락</td><td style='text-align: left; vertical-align: bottom; border-top: 1px solid #000000; border-right: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000'>O</td></tr><tr><td style='background-color: #C0CDEF; text-align: left; vertical-align: bottom; border-top: 1px solid #000000; border-right: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000'>이미지 관련 제한사항</td><td style='text-align: left; vertical-align: bottom; border-top: 1px solid #000000; border-right: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000'>비지원 위성사진 형식 사용 시 분석 부가</td><td style='text-align: left; vertical-align: bottom; border-top: 1px solid #000000; border-right: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000'>X</td></tr><tr><td style='background-color: #C0CDEF; text-align: left; vertical-align: bottom; border-top: 1px solid #000000; border-right: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000'>주소 입력 오류</td><td style='text-align: left; vertical-align: bottom; border-top: 1px solid #000000; border-right: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000'>부정확한 주소 입력
위성 미지원 범위 주소
도로명/지번 주소 혼용 오류 발견</td><td style='text-align: left; vertical-align: bottom; border-top: 1px solid #000000; border-right: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000'>X</td></tr></table>",
                    fileId = 2411,
                    volumeId = 428019990,
                    fileType = "Excel",
                    fileName = "모델별 분석.xlsx",
                    filePath = @"G:\내 드라이브\H에너지\모델별 분석.xlsx"
                },
                target_program = new
                {
                    context = "다음은 AI 모델 분석에 관한 내용이다.",
                    fileId = 2359,
                    volumeId = 428019990,
                    fileType = "Word",
                    fileName = "AI 분석 보고서.docx",
                    filePath = @"G:\내 드라이브\H에너지\AI 분석 보고서.docx"
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
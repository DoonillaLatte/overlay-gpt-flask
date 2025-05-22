using System;
using System.Threading.Tasks;
using SocketIOClient;
using System.Text.Json;
using System.IO;
using SocketIO.Core;

class Program
{
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

        client.OnConnected += async (sender, e) =>
        {
            Console.WriteLine("서버에 연결되었습니다.");
            
            // Excel 파일 경로
            string excelFilePath = Path.Combine("test_excel_file", "사람정보.xlsx");
            
            if (!File.Exists(excelFilePath))
            {
                Console.WriteLine($"Excel 파일을 찾을 수 없습니다: {excelFilePath}");
                return;
            }

            // Excel 파일을 바이트 배열로 읽기
            byte[] excelBytes = File.ReadAllBytes(excelFilePath);
            string base64Excel = Convert.ToBase64String(excelBytes);
            
            // 테스트용 요청 데이터
            var request = new
            {
                command = "search_similar_context",
                chat_id = 1,
                prompt = "Excel 데이터 분석",
                request_type = 1, // 1: explain
                description = "사람 정보 데이터 분석",
                current_program = new
                {
                    id = 1,
                    type = "excel",
                    context = "사람 정보"
                },
                target_program = new
                {
                    id = 2,
                    type = "word",
                    context = "분석 보고서"
                },
                file_data = new
                {
                    filename = "사람정보.xlsx",
                    content = base64Excel,
                    content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                }
            };

            Console.WriteLine("요청 데이터:");
            Console.WriteLine(JsonSerializer.Serialize(request, new JsonSerializerOptions { WriteIndented = true }));
            
            Console.WriteLine("요청 전송 중...");
            await client.EmitAsync("message", request);
            Console.WriteLine("요청 전송 완료");
        };

        client.On("message_response", response =>
        {
            var result = response.GetValue<dynamic>();
            Console.WriteLine($"응답 수신:");
            Console.WriteLine($"Chat ID: {result.chat_id}");
            Console.WriteLine($"Status: {result.status}");
            Console.WriteLine($"Response: {result.response}");
        });

        client.OnError += (sender, e) =>
        {
            Console.WriteLine($"에러 발생: {e}");
        };

        client.OnDisconnected += (sender, e) =>
        {
            Console.WriteLine("서버와 연결이 끊어졌습니다.");
        };

        try
        {
            Console.WriteLine("서버 연결 시도 중...");
            await client.ConnectAsync();
            Console.WriteLine("서버 연결 성공");
            Console.WriteLine("종료하려면 아무 키나 누르세요...");
            Console.ReadKey();
        }
        catch (Exception ex)
        {
            Console.WriteLine($"연결 중 에러 발생: {ex.Message}");
        }
    }
}
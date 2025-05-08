import getpass

from mcp_query_table.server import serve


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="query table from website",
    )

    parser.add_argument("--format", type=str, help="输出格式",
                        default='markdown', choices=['markdown', 'csv', 'json'])
    parser.add_argument("--endpoint", type=str, help="浏览器CDP地址/WS地址",
                        nargs="?", default=r'http://127.0.0.1:9222')
    parser.add_argument("--executable_path", type=str, help="浏览器路径",
                        nargs="?", default=r'C:\Program Files\Google\Chrome\Application\chrome.exe')
    parser.add_argument("--user_data_dir", type=str, help="浏览器用户数据目录",
                        nargs="?", default=rf'C:\Users\{getpass.getuser()}\AppData\Local\Google\Chrome\User Data\Default')
    parser.add_argument("--transport", type=str, help="传输类型",
                        default='stdio', choices=['stdio', 'sse'])
    parser.add_argument("--host", type=str, help="MCP服务端绑定地址",
                        default='0.0.0.0')
    parser.add_argument("--port", type=int, help="MCP服务端绑定端口",
                        default='8000')
    args = parser.parse_args()
    serve(args.format, args.endpoint,
          args.executable_path, args.user_data_dir,
          args.transport, args.host, args.port)


if __name__ == "__main__":
    main()

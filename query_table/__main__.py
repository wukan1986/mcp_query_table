from query_table.server import serve


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="query table from website",
    )

    parser.add_argument("--format", type=str, help="输出格式",
                        default='markdown', choices=['markdown', 'csv', 'json'])
    parser.add_argument("--cdp_port", type=int, help="浏览器远程调试端口",
                        default=9222)
    parser.add_argument("--browser_path", type=str, help="浏览器类型",
                        default=r'C:\Program Files\Google\Chrome\Application\chrome.exe')

    parser.add_argument("--transport", type=str, help="传输类型",
                        default='stdio', choices=['stdio', 'sse'])
    parser.add_argument("--mcp_host", type=str, help="MCP服务端地址",
                        default='0.0.0.0')
    parser.add_argument("--mcp_port", type=int, help="MCP服务端端口",
                        default='8000')
    args = parser.parse_args()
    serve(args.format, args.cdp_port, args.browser_path, args.transport, args.mcp_host, args.mcp_port)


if __name__ == "__main__":
    main()

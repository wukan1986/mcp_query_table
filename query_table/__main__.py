from .server import serve


def main():
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(
        description="query table from website",
    )

    parser.add_argument("--format", type=str, help="输出格式",
                        default='markdown', choices=['markdown', 'csv', 'json'])
    parser.add_argument("--port", type=int, help="浏览器远程调试端口",
                        default=9222)
    parser.add_argument("--browser_path", type=str, help="浏览器类型",
                        default=r'C:\Program Files\Google\Chrome\Application\chrome.exe')

    args = parser.parse_args()
    asyncio.run(serve(args.format, args.port, args.browser_path))


if __name__ == "__main__":
    main()

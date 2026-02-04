start uv run python -m streamlit run app.py --server.enableStaticServing=true --theme.codeFont="SimSun, monospace" --server.port=51015
cd ..
start uv run python -m mcp_query_table --format markdown --transport sse --port 8000 --endpoint --executable_path --user_data_dir
pause
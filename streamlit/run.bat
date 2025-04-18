CALL d:\Users\Kan\miniconda3\Scripts\activate.bat d:\Users\Kan\miniconda3\envs\py312
start streamlit run app.py --server.enableStaticServing=true --theme.codeFont="SimSun, monospace" --server.port=51015
cd ..
start python -m mcp_query_table --format markdown --transport sse --port 8000 --endpoint --executable_path --user_data_dir
pause
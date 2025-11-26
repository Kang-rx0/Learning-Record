# pip install -U langchain-openai langchain-core langchain langchain-community langchain-experimental langchain-text-splitters langchain-classic

# streamlit run LLM/Langchain/LangChain09.py

import streamlit as st #用来快速构建前端页面
from PyPDF2 import PdfReader # PDF文档读取、处理的依赖库
from langchain_text_splitters import RecursiveCharacterTextSplitter # LangChain封装的文档切分库
from langchain_core.prompts import ChatPromptTemplate 
from langchain_community.vectorstores import FAISS # FAISS向量数据库,保存文本块向量
from langchain_core.tools import create_retriever_tool # 检索用的
# 这里由于LangChain的一些更新，使用 langchain_classic 来获取传统的 Agent API
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_community.embeddings import DashScopeEmbeddings  # 阿里的embedding模型，这里用的是另一个
from langchain.chat_models import init_chat_model 
from modelscope import AutoTokenizer, snapshot_download 

import argparse
def parse_args():
    parse = argparse.ArgumentParser(description="RAG")
    parse.add_argument("--embedding_model", type=str, default="", help="向量模型名称")
    parse.add_argument("--embed_api_key", type=str, default="", help="向量模型API Key")
    parse.add_argument("--embedding_model_dir", type=str, default="", help="向量模型目录")
    parse.add_argument("--model", type=str, default="", help="大语言模型名称")
    parse.add_argument("--base_url", type=str, default="", help="请求url")
    parse.add_argument("--api_key", type=str, default="", help="API Key")
    parse.add_argument("--embedding_vector_dir", type=str, default="", help="向量数据库存储目录")
    parse.add_argument("--model_provider", type=str, default="", help="模型提供商")
    parse.add_argument("--chunk_size", type=int, default=1000, help="文本块大小")
    parse.add_argument("--chunk_overlap", type=int, default=200, help="文本块重叠大小")
    parse.add_argument("--if_download_model", type=bool, default=False, help="是否下载模型到本地")
    args = parse.parse_args()
    return args

def load_model(args):
    # 初始化向量模型,这是阿里云百炼的
    embeddings = DashScopeEmbeddings(
        model=args.embedding_model,
        dashscope_api_key=args.embed_api_key
    )
    # if args.if_download_model:
    #     model_dir = snapshot_download(model_id=args.embedding_model, cache_dir=args.embedding_model_dir)
    #     embeddings = AutoTokenizer.from_pretrained(model_dir, device_map="auto", dtype="auto")
    # else:
    #     embeddings = AutoTokenizer.from_pretrained(args.embedding_model_dir+'/'+args.embedding_model, device_map="auto", dtype="auto")

    #初始化大语言模型
    llm = init_chat_model(
        model=args.model, # 模型名称
        model_provider=args.model_provider, # 模型提供商
        base_url=args.base_url, #请求url
        api_key=args.api_key, 
    )
    return embeddings, llm

#读取pdf上传的内容
def pdf_read(pdf_doc):
    text = ""
    for pdf in pdf_doc:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_chunks(text,args):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap)
    chunks = text_splitter.split_text(text)
    return chunks

# 将向量存储在本地FAISS数据库中
def vector_store(text_chunks, embeddings,args):
    vector_store = FAISS.from_texts(text_chunks, embeddings)
    #vector_store = FAISS.from_documents(text_chunks, embeddings)
    vector_store.save_local(args.embedding_vector_dir)

import os
# 构建知识库回答逻辑链
def check_database_exists(args):
    """检查FAISS数据库是否存在"""
    return os.path.exists(args.embedding_vector_dir) and os.path.exists(args.embedding_vector_dir+"/index.faiss")

def user_input(user_question, embeddings, llm,args):
    # 检查数据库是否存在
    if not check_database_exists(args):
        st.error("❌ 请先上传PDF文件并点击'Submit & Process'按钮来处理文档！")
        st.info("  步骤：1️⃣ 上传PDF → 2️⃣ 点击处理 → 3️⃣ 开始提问")
        return

    try:
        # 加载FAISS数据库
        new_db = FAISS.load_local(args.embedding_vector_dir, embeddings, allow_dangerous_deserialization=True)
        # 将数据转化为LangChain检索工具
        retriever = new_db.as_retriever() 
        
        # 使用LangChain的create_retriever_tool构建内容检索工具
        retrieval_chain = create_retriever_tool(retriever, "pdf_extractor",
                                                "This tool is to give answer to queries from the pdf")
        get_conversational_chain(retrieval_chain, user_question,llm)

    except Exception as e:
        st.error(f"❌ 加载数据库时出错: {str(e)}") # 前端界面报错
        st.info("请重新处理PDF文件") # 前端界面info提示

def get_conversational_chain(tools, querys, llm):
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """你是AI助手，请根据提供的上下文回答问题，确保提供所有细节，如果答案不在上下文中，请说"答案不在上下文中"，不要提供错误的答案""",
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    tool = [tools]
    agent = create_tool_calling_agent(llm, tool, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tool, verbose=True)

    response = agent_executor.invoke({"input": querys})
    print(response)
    st.write("  回答: ", response['output'])

def UI(args,embeddings,llm):
    st.set_page_config("  RAG知识库系统")
    st.header("  RAG知识库系统")

    # 显示数据库状态
    col1, col2 = st.columns([3, 1])

    with col1:
        if check_database_exists(args):
            pass
        else:
            st.warning("⚠️ 请先上传并处理PDF文件")

    with col2:
        if st.button(" ️ 清除数据库"):
            try:
                import shutil
                if os.path.exists(args.embedding_vector_dir):
                    shutil.rmtree(args.embedding_vector_dir)
                st.success("数据库已清除")
                st.rerun()
            except Exception as e:
                st.error(f"清除失败: {e}")

    # 用户问题输入
    user_question = st.text_input("  请输入问题",
                                  placeholder="例如：这个文档的主要内容是什么？",
                                  disabled=not check_database_exists(args))

    if user_question:
        if check_database_exists(args):
            with st.spinner("  AI正在分析文档..."):
                user_input(user_question, embeddings, llm, args)  # user_input里包含了将user_question输入到大模型里的代码
        else:
            st.error("❌ 请先上传并处理PDF文件！")

    # 侧边栏
    with st.sidebar:
        st.title("  文档管理")

        # 显示当前状态
        if check_database_exists(args):
            st.success("✅ 数据库状态：已就绪")
        else:
            st.info("  状态：等待上传PDF")

        st.markdown("---")

        # 文件上传
        pdf_doc = st.file_uploader(
            "  上传PDF文件",
            accept_multiple_files=True,
            type=['pdf'],
            help="支持上传多个PDF文件"
        )

        if pdf_doc:
            st.info(f"  已选择 {len(pdf_doc)} 个文件")
            for i, pdf in enumerate(pdf_doc, 1):
                st.write(f"{i}. {pdf.name}")

        # 处理按钮
        process_button = st.button(
            "  提交并处理",
            disabled=not pdf_doc,
            use_container_width=True
        )

        if process_button:
            if pdf_doc:
                with st.spinner("  正在处理PDF文件..."):
                    try:
                        # 读取PDF内容
                        raw_text = pdf_read(pdf_doc)

                        if not raw_text.strip():
                            st.error("❌ 无法从PDF中提取文本，请检查文件是否有效")
                            return

                        # 分割文本
                        text_chunks = get_chunks(raw_text,args)
                        st.info(f"  文本已分割为 {len(text_chunks)} 个片段")

                        # 创建向量数据库
                        vector_store(text_chunks,embeddings,args)

                        st.success("✅ PDF处理完成！现在可以开始提问了")
                        st.balloons()
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ 处理PDF时出错: {str(e)}")
            else:
                st.warning("⚠️ 请先选择PDF文件")

        # 使用说明
        with st.expander("  使用说明"):
            st.markdown("""
                **步骤：**
                1.   上传一个或多个PDF文件
                2.   点击"Submit & Process"处理文档
                3.   在主页面输入您的问题
                4.   AI将基于PDF内容回答问题
    
                **提示：**
                - 支持多个PDF文件同时上传
                - 处理大文件可能需要一些时间
                - 可以随时清除数据库重新开始
                """)

def main(args):
    # 加载模型
    embeddings, llm = load_model(args)

    # 启动UI界面
    UI(args,embeddings,llm)
    
if __name__ == "__main__":
    args = parse_args()
    main(args)
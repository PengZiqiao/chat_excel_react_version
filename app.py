import gradio as gr
from agent.react_agent import DataframeAgent
import pandas as pd

# 定义处理文件上传的函数
def handle_file_upload(file):
    # 输出上传的文件名
    print(f"File uploaded: {file.name}")

    # 读取文件并保存到df，生成agent
    global df, agent
    df = pd.read_excel(file)
    agent = DataframeAgent(df)

# 定义echo函数，用于返回接收到的消息
def chat(message, history):
    history = history + [[message, None]]

    thoughts = ''
    action = ''
    plot_path = None

    # 返回接收到的消息，作为聊天交互的一部分
    reply_generated = agent(message, history)
    try:
        while True:
            text = next(reply_generated)
            if '- Reasoning: ' in text:
                thoughts = text
            elif '- Tool: ' in text:
                action = text
                if '图片文件已保存' in text:
                    plot_path = 'plot.png'

            yield '', history, thoughts+action, plot_path
    except StopIteration as e:
        final_answer = e.value
        if '请查看右侧图片' in final_answer:
            plot_path = 'plot.png'
        history[-1][1] = final_answer
        yield '', history, thoughts+action, plot_path


with gr.Blocks() as demo:
    file_input = gr.File()
    file_input.upload(handle_file_upload, file_input)

    # 如果有文件上传，初始化一个聊天界面；如果没有文件上传，显示提示信息
    @gr.render(inputs=file_input)
    def show_chat(file):
        if file:
            with gr.Blocks(fill_height=True):
                with gr.Row():
                    with gr.Column():
                        chatbot = gr.Chatbot(show_label=False)
                        msg = gr.Textbox(placeholder="请输入问题", show_label=False)
                        clear = gr.ClearButton([chatbot, msg])
                    with gr.Column():
                        plot_image = gr.Image(type="filepath", show_label=False, interactive=False)
                        thoughts = gr.Markdown()
                msg.submit(chat, [msg, chatbot], [msg, chatbot, thoughts, plot_image])
        else: 
            gr.Markdown("请上传一个excel文件")
    
    

demo.queue().launch()
import re
import json
from pathlib import Path
from string import Template
from agent.tools import tools_description, generate_tools_map
from agent.model import client

class Agent:
        def __init__(self, tools_description, tools_map, prompt_template_name=None):
             self.tools_decription = tools_description
             self.tools_map = tools_map
             self.prompt_template_name = prompt_template_name
             if prompt_template_name:
                 self.template = self.__load_template(prompt_template_name)
             else:
                 self.template = None
        # 加载模板
        def __load_template(self, template_name):
            current_dir = Path(__file__).resolve().parent
            templates_dir = current_dir / '..' / 'templates'
            template_path = templates_dir / f'{template_name}.txt'
            return Template(template_path.read_text())
        # 生成prompt
        def __generate_prompt(self, query='', prompt_template_name = None, **kwargs):
            if prompt_template_name:
                template = self.__load_template(prompt_template_name)
            else:
                template = self.template
            
            return template.substitute(query=query, **kwargs)
        
        # 将回复转为字典
        def __json_loads(self, response):
            print(response)
            pattern = re.compile(r'.*?```json\n(.*)\n```.*?', re.DOTALL)
            match = pattern.search(response)
            json_text = match.group(1).strip()
            try:
                return json.loads(json_text)
            except Exception as e:
                print(e)
                print(json_text)
                return None
            
        # 调用大语言模型    
        def chat_with_llm(self, messages):
            response = client.chat.completions.create(
                model='glm-4-9b',
                messages=messages,
                temperature=0,
                max_tokens=4096,
            ).choices[0].message.content

            response = self.__json_loads(response)

            return response
        
        # 解析响应
        def __parse_thoughts(self, response):
            try:
                reasoning = response.get('reasoning')
                observation = response.get('observation')
                prompt_template = self.__load_template('thoughts_template')
                prompt = prompt_template.substitute(reasoning=reasoning, observation=observation)

                return prompt
            except Exception as e:
                print(f'\033[1;31m Error: {e} \033[0m')
                return str(e)
            
        def __parse_action(self, response):
            try:
                action = response.get('action')
                action_name = action.get('name')
                action_args = action.get('args')

                return action_name, action_args
            except Exception as e:
                print(f'\033[1;31m Error: {e} \033[0m')
                return str(e), None
            
        def agent_execute(self, query, max_request_time=10, **template_kargs):
            cur_request_time = 0

            # 第一次请求prompt
            prompt = self.__generate_prompt(query, tools_description=self.tools_decription, **template_kargs)
            messages = [
                {"role": "user", "content": prompt}
            ]


            while cur_request_time < max_request_time:
                cur_request_time += 1

                # 发送请求
                response = self.chat_with_llm(messages)

                # 解析思考
                thoughts = self.__parse_thoughts(response)
                yield thoughts

                # 解析动作
                action_name, action_args = self.__parse_action(response)

                # 判断是否结束
                if action_name == 'finish':
                    final_answer = action_args.get('answer')
                    # print(f' Final Answer: \n {final_answer}')
                    return final_answer
                else:
                    try:
                        func = self.tools_map.get(action_name)
                        func_result = func(**action_args)

                        action_template = self.__load_template('action_template')
                        agent_scratch = action_template.substitute(action_name=action_name, action_args=action_args, action_result=func_result)
                        yield agent_scratch
                        agent_scratch = f'action_name:{action_name}\naction_args:{action_args}\naction_result:{func_result}'
                    except Exception as e:
                        print(f'\033[1;31m Error: {e} \033[0m')
                        agent_scratch = f'action_result: {e}'
                
                    # 更新prompt
                    messages = [
                        {"role": "user", "content": f'{prompt}\n## agent_scratchpad:\n{thoughts}\n{agent_scratch}'}
                    ]

class DataframeAgent(Agent):
    def __init__(self, df):
        self. df_head = df.head().to_markdown()
        tools_map = generate_tools_map(df)
        super().__init__(
            tools_description=tools_description, 
            tools_map=tools_map,
            prompt_template_name='df_react_agent'
        )

    def __call__(self, query, history=[]):
        history_text = ''
        if history:
            for user, assistant in history:
                history_text += f'query: {user}\nanswer: {assistant}\n'
        gen = self.agent_execute(query, df_head=self.df_head, history=history_text)
        
        # 循环输出thoughts 与 action，最后输出final answer
        try:
            while True:
                yield next(gen)
        except StopIteration as e:
            return e.value
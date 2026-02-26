import numpy as np
import roslibpy
import os, time, ast, re, argparse, math
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

MODEL_OPTIONS = ['gpt-4o', 'custom', 'training']

class LLMResourceManagement():
    def __init__(self,
                 openai_token,
                 model,
                 model_dir=None,
                 quant=False,
                 ros=None,
                 host_ip='192.168.192.105'):
        
        # Low-Level controller parameter
        self.default_rs_controller_params = {
            "weight_mec": 1.0,
            "weight_com": 1.0,
            "v_min": 0.5,
            "v_max": 6.0,
        }

        if ros:
            self.ros = ros
        else:
            self.ros = roslibpy.Ros(host=host_ip, port=8805)
        
        # LLM configuration
        self.openai_token = openai_token
        self.quant = quant
        self.llm, self.custom, self.use_openai = self.init_llm(model=model, model_dir=model_dir, openai_token=openai_token)

        # Analysis RAG
        self.base_memory, self.vector_index = self.load_memory(openai_token=self.openai_token)
        # Decision RAG
        self.decision_index = self.load_decision_mem(openai_api_key=self.openai_token)
    
    def init_llm(self, model: str, model_dir:str, openai_token: str) -> tuple:
        use_openai = False
        custom = False
        llm = None

        if model not in MODEL_OPTIONS:
            raise ValueError(f"Model {model} not supported. Please use one of {MODEL_OPTIONS}")
        if model == 'gpt-4o':
            use_openai = True
            llm = ChatOpenAI(model_name="gpt-4o", openai_api_key=openai_token)
        elif model == 'custom':
            if self.quant:
                # todo
                pass   
            else:
                # todo
                pass  
        elif model == 'training':
            print("Not setting a model because we are training and using llm_rs just as a vessel to interact with ROS and utils.")
        else:
            raise ValueError(f"Something went wrong with the model selection: {model}")
        return llm, custom, use_openai
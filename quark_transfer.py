#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
夸克网盘转存分享工具 - Python版本
用法: python3 quark_transfer.py <cookie> <share_id> [--debug]
"""

import sys
import time
import json
import argparse
import requests
from typing import Dict, List, Optional, Tuple


class Colors:
    """终端颜色"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


class QuarkTransfer:
    """夸克网盘转存类"""
    
    def __init__(self, cookie: str, debug: bool = False):
        self.cookie = cookie
        self.debug = debug
        self.session = requests.Session()
        
        # 设置默认请求头
        self.session.headers.update({
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Content-Type": "application/json;charset=UTF-8",
            "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Referer": "https://pan.quark.cn/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Cookie": cookie
        })
        
    def log(self, message: str, color: str = Colors.NC):
        """输出日志"""
        print(f"{color}{message}{Colors.NC}")
        
    def debug_log(self, message: str):
        """调试日志"""
        if self.debug:
            print(f"{Colors.BLUE}[DEBUG] {message}{Colors.NC}", file=sys.stderr)
            
    def get_timestamp(self) -> int:
        """获取13位时间戳"""
        return int(time.time() * 1000)
        
    def get_stoken(self, share_id: str) -> Tuple[bool, str, str]:
        """
        获取stoken
        返回: (成功标志, stoken, 错误信息)
        """
        url = "https://drive-pc.quark.cn/1/clouddrive/share/sharepage/token"
        params = {"pr": "ucpro", "fr": "pc", "uc_param_str": ""}
        data = {"passcode": "", "pwd_id": share_id}
        
        try:
            response = self.session.post(url, params=params, json=data)
            result = response.json()
            
            self.debug_log(f"Stoken响应: {json.dumps(result, ensure_ascii=False)}")
            
            if result.get("status") == 200:
                stoken = result.get("data", {}).get("stoken", "")
                return True, stoken.replace(" ", "+"), ""
            else:
                return False, "", result.get("message", "未知错误")
        except Exception as e:
            return False, "", str(e)
            
    def get_share_detail(self, share_id: str, stoken: str) -> Tuple[bool, Dict, str]:
        """
        获取分享详情
        返回: (成功标志, 详情数据, 错误信息)
        """
        url = "https://drive-pc.quark.cn/1/clouddrive/share/sharepage/detail"
        params = {
            "pr": "ucpro",
            "fr": "pc",
            "uc_param_str": "",
            "pwd_id": share_id,
            "stoken": stoken,
            "pdir_fid": "0",
            "force": "0",
            "_page": "1",
            "_size": "100",
            "_fetch_banner": "1",
            "_fetch_share": "1",
            "_fetch_total": "1",
            "_sort": "file_type:asc,updated_at:desc"
        }
        
        try:
            response = self.session.get(url, params=params)
            result = response.json()
            
            self.debug_log(f"分享详情响应: {json.dumps(result, ensure_ascii=False)}")
            
            if result.get("status") == 200:
                return True, result.get("data", {}), ""
            else:
                return False, {}, result.get("message", "未知错误")
        except Exception as e:
            return False, {}, str(e)
            
    def save_share(self, share_id: str, stoken: str, fid_list: List[str], 
                   fid_token_list: List[str]) -> Tuple[bool, str, str]:
        """
        转存分享
        返回: (成功标志, task_id, 错误信息)
        """
        url = "https://drive-pc.quark.cn/1/clouddrive/share/sharepage/save"
        params = {"pr": "ucpro", "fr": "pc", "uc_param_str": ""}
        data = {
            "pwd_id": share_id,
            "stoken": stoken,
            "fid_list": fid_list,
            "fid_token_list": fid_token_list,
            "to_pdir_fid": "0"
        }
        
        self.debug_log(f"转存请求: {json.dumps(data, ensure_ascii=False)}")
        
        try:
            response = self.session.post(url, params=params, json=data)
            result = response.json()
            
            self.debug_log(f"转存响应: {json.dumps(result, ensure_ascii=False)}")
            
            if result.get("status") == 200:
                task_id = result.get("data", {}).get("task_id", "")
                return True, task_id, ""
            else:
                return False, "", result.get("message", "未知错误")
        except Exception as e:
            return False, "", str(e)
            
    def get_task_status(self, task_id: str, retry_index: int = 0) -> Tuple[bool, Dict, str]:
        """
        获取任务状态
        返回: (成功标志, 任务数据, 错误信息)
        """
        url = "https://drive-pc.quark.cn/1/clouddrive/task"
        params = {
            "pr": "ucpro",
            "fr": "pc",
            "uc_param_str": "",
            "task_id": task_id,
            "retry_index": str(retry_index),
            "__dt": "21192",
            "__t": str(self.get_timestamp())
        }
        
        try:
            response = self.session.get(url, params=params)
            result = response.json()
            
            self.debug_log(f"任务状态响应: {json.dumps(result, ensure_ascii=False)}")
            
            if result.get("status") == 200:
                return True, result.get("data", {}), ""
            else:
                return False, {}, result.get("message", "未知错误")
        except Exception as e:
            return False, {}, str(e)
            
    def wait_for_task(self, task_id: str, max_retries: int = 50) -> Tuple[bool, Dict, str]:
        """
        等待任务完成
        返回: (成功标志, 任务数据, 错误信息)
        """
        for retry_index in range(max_retries):
            success, data, error = self.get_task_status(task_id, retry_index)
            
            if not success:
                return False, {}, error
                
            if data.get("status") == 2:  # 任务完成
                return True, data, ""
                
            print(".", end="", flush=True)
            time.sleep(2)
            
        return False, {}, "任务超时"
        
    def create_share(self, fid_list: List[str], title: str) -> Tuple[bool, str, str]:
        """
        创建分享
        返回: (成功标志, task_id, 错误信息)
        """
        url = "https://drive-pc.quark.cn/1/clouddrive/share"
        params = {"pr": "ucpro", "fr": "pc", "uc_param_str": ""}
        data = {
            "fid_list": fid_list,
            "title": title,
            "url_type": 1,
            "expired_type": 1
        }
        
        self.debug_log(f"分享请求: {json.dumps(data, ensure_ascii=False)}")
        
        try:
            response = self.session.post(url, params=params, json=data)
            result = response.json()
            
            self.debug_log(f"分享响应: {json.dumps(result, ensure_ascii=False)}")
            
            if result.get("status") == 200:
                task_id = result.get("data", {}).get("task_id", "")
                return True, task_id, ""
            else:
                return False, "", result.get("message", "未知错误")
        except Exception as e:
            return False, "", str(e)
            
    def get_share_password(self, share_id: str) -> Tuple[bool, Dict, str]:
        """
        获取分享密码
        返回: (成功标志, 密码数据, 错误信息)
        """
        url = "https://drive-pc.quark.cn/1/clouddrive/share/password"
        params = {"pr": "ucpro", "fr": "pc", "uc_param_str": ""}
        data = {"share_id": share_id}
        
        self.debug_log(f"密码请求: {json.dumps(data, ensure_ascii=False)}")
        
        try:
            response = self.session.post(url, params=params, json=data)
            result = response.json()
            
            self.debug_log(f"密码响应: {json.dumps(result, ensure_ascii=False)}")
            
            if result.get("status") == 200:
                return True, result.get("data", {}), ""
            else:
                return False, {}, result.get("message", "未知错误")
        except Exception as e:
            return False, {}, str(e)
            
    def transfer(self, share_id: str) -> Tuple[bool, Dict, str]:
        """
        执行完整的转存流程
        返回: (成功标志, 结果数据, 错误信息)
        """
        self.log("=" * 50, Colors.GREEN)
        self.log("夸克网盘转存分享工具 - Python版", Colors.GREEN)
        self.log("=" * 50, Colors.GREEN)
        self.log(f"开始处理分享: {share_id}", Colors.YELLOW)
        print()
        
        # 步骤1: 获取stoken
        self.log("[1/6] 获取stoken...", Colors.YELLOW)
        success, stoken, error = self.get_stoken(share_id)
        if not success:
            return False, {}, f"获取stoken失败: {error}"
        self.log("✓ 获取stoken成功", Colors.GREEN)
        
        # 步骤2: 获取分享详情
        self.log("[2/6] 获取分享详情...", Colors.YELLOW)
        success, detail_data, error = self.get_share_detail(share_id, stoken)
        if not success:
            return False, {}, f"获取分享详情失败: {error}"
            
        title = detail_data.get("share", {}).get("title", "")
        file_list = detail_data.get("list", [])
        
        if not file_list:
            return False, {}, "没有找到可转存的文件"
            
        fid_list = [item.get("fid") for item in file_list]
        fid_token_list = [item.get("share_fid_token") for item in file_list]
        
        self.log("✓ 获取分享详情成功", Colors.GREEN)
        self.log(f"  标题: {title}")
        self.log(f"  文件数量: {len(fid_list)}")
        
        # 步骤3: 转存分享
        self.log("[3/6] 转存资源...", Colors.YELLOW)
        success, task_id, error = self.save_share(share_id, stoken, fid_list, fid_token_list)
        if not success:
            return False, {}, f"转存失败: {error}"
        self.log(f"✓ 转存任务已创建: {task_id}", Colors.GREEN)
        
        # 步骤4: 等待转存完成
        self.log("[4/6] 等待转存完成...", Colors.YELLOW)
        success, task_data, error = self.wait_for_task(task_id)
        if not success:
            return False, {}, f"等待转存完成失败: {error}"
        print()  # 换行
        self.log("✓ 转存完成", Colors.GREEN)
        
        save_as_fids = task_data.get("save_as", {}).get("save_as_top_fids", [])
        if not save_as_fids:
            return False, {}, "转存后未获取到文件ID"
            
        # 步骤5: 创建分享
        self.log("[5/6] 创建分享链接...", Colors.YELLOW)
        success, share_task_id, error = self.create_share(save_as_fids, title)
        if not success:
            return False, {}, f"创建分享失败: {error}"
        self.log(f"✓ 分享任务已创建: {share_task_id}", Colors.GREEN)
        
        # 步骤6: 等待分享完成
        self.log("[6/6] 等待分享完成...", Colors.YELLOW)
        success, share_task_data, error = self.wait_for_task(share_task_id)
        if not success:
            return False, {}, f"等待分享完成失败: {error}"
        print()  # 换行
        self.log("✓ 分享完成", Colors.GREEN)
        
        new_share_id = share_task_data.get("share_id", "")
        if not new_share_id:
            return False, {}, "分享后未获取到分享ID"
            
        # 获取分享密码
        self.log("获取分享密码...", Colors.YELLOW)
        success, password_data, error = self.get_share_password(new_share_id)
        
        # 构建结果
        result = {
            "title": title,
            "share_id": new_share_id,
            "share_url": password_data.get("share_url") or f"https://pan.quark.cn/s/{new_share_id}",
            "code": password_data.get("code", ""),
            "fid_list": save_as_fids
        }
        
        return True, result, ""


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="夸克网盘转存分享工具 - Python版",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 quark_transfer.py "your_cookie" "share_id"
  python3 quark_transfer.py "your_cookie" "share_id" --debug
        """
    )
    parser.add_argument("cookie", help="夸克网盘Cookie")
    parser.add_argument("share_id", help="分享ID")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    
    args = parser.parse_args()
    
    # 检查requests库
    try:
        import requests
    except ImportError:
        print(f"{Colors.RED}错误: 需要安装 requests 库{Colors.NC}")
        print("请运行: pip3 install requests")
        sys.exit(1)
    
    # 创建转存实例
    transfer = QuarkTransfer(args.cookie, args.debug)
    
    # 执行转存
    success, result, error = transfer.transfer(args.share_id)
    
    if not success:
        print()
        print(f"{Colors.RED}转存失败: {error}{Colors.NC}")
        sys.exit(1)
    
    # 输出结果
    print()
    print(f"{Colors.GREEN}{'=' * 50}{Colors.NC}")
    print(f"{Colors.GREEN}转存完成{Colors.NC}")
    print(f"{Colors.GREEN}{'=' * 50}{Colors.NC}")
    print(f"{Colors.GREEN}分享链接:{Colors.NC} {result['share_url']}")
    
    if result.get('code'):
        print(f"{Colors.GREEN}提取码:{Colors.NC} {result['code']}")
    else:
        print(f"{Colors.YELLOW}提取码:{Colors.NC} 无需提取码")
        
    print(f"{Colors.GREEN}标题:{Colors.NC} {result['title']}")
    print(f"{Colors.GREEN}分享ID:{Colors.NC} {result['share_id']}")
    
    if result.get('fid_list'):
        print(f"{Colors.GREEN}文件ID:{Colors.NC} {','.join(result['fid_list'])}")
    
    print()


if __name__ == "__main__":
    main()

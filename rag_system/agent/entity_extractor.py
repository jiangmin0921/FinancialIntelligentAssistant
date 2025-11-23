"""
实体提取和参数验证模块（V1.1新增）
支持结构化实体提取和参数自动修正
"""

import re
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class EmployeeEntity:
    """员工实体"""
    name: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None


@dataclass
class DateRangeEntity:
    """日期范围实体"""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    month: Optional[int] = None
    year: Optional[int] = None


class EntityExtractor:
    """实体提取器"""
    
    def __init__(self, user_context: Optional[Dict] = None):
        """
        初始化实体提取器
        
        Args:
            user_context: 用户上下文
        """
        self.user_context = user_context or {}
    
    def extract_date_range(self, text: str) -> DateRangeEntity:
        """
        提取日期范围
        
        支持格式：
        - "3月份" → 2024-03-01 到 2024-03-31
        - "今年上半年" → 2024-01-01 到 2024-06-30
        - "上个月" → 上个月的第一天到最后一天
        """
        entity = DateRangeEntity()
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # 匹配"X月份"
        month_match = re.search(r'(\d+)月份?', text)
        if month_match:
            month = int(month_match.group(1))
            if 1 <= month <= 12:
                entity.month = month
                entity.year = current_year
                entity.start_date = f"{current_year}-{month:02d}-01"
                # 计算该月最后一天
                if month == 12:
                    entity.end_date = f"{current_year}-12-31"
                else:
                    next_month = datetime(current_year, month + 1, 1)
                    last_day = (next_month - timedelta(days=1)).day
                    entity.end_date = f"{current_year}-{month:02d}-{last_day}"
                return entity
        
        # 匹配"今年上半年"
        if "上半年" in text or "前半年" in text:
            entity.start_date = f"{current_year}-01-01"
            entity.end_date = f"{current_year}-06-30"
            return entity
        
        # 匹配"今年下半年"
        if "下半年" in text or "后半年" in text:
            entity.start_date = f"{current_year}-07-01"
            entity.end_date = f"{current_year}-12-31"
            return entity
        
        # 匹配"上个月"
        if "上个月" in text or "上月" in text:
            if current_month == 1:
                last_month = 12
                last_year = current_year - 1
            else:
                last_month = current_month - 1
                last_year = current_year
            
            entity.month = last_month
            entity.year = last_year
            entity.start_date = f"{last_year}-{last_month:02d}-01"
            # 计算上个月最后一天
            first_day_this_month = datetime(current_year, current_month, 1)
            last_day_last_month = (first_day_this_month - timedelta(days=1)).day
            entity.end_date = f"{last_year}-{last_month:02d}-{last_day_last_month}"
            return entity
        
        # 匹配"本月"或"这个月"
        if "本月" in text or "这个月" in text:
            entity.month = current_month
            entity.year = current_year
            entity.start_date = f"{current_year}-{current_month:02d}-01"
            # 计算本月最后一天
            if current_month == 12:
                entity.end_date = f"{current_year}-12-31"
            else:
                next_month = datetime(current_year, current_month + 1, 1)
                last_day = (next_month - timedelta(days=1)).day
                entity.end_date = f"{current_year}-{current_month:02d}-{last_day}"
            return entity
        
        return entity
    
    def extract_employee(self, text: str) -> EmployeeEntity:
        """
        提取员工信息
        
        支持：
        - 员工姓名
        - 员工工号（E001格式）
        - 部门名称（需要后续查询）
        """
        entity = EmployeeEntity()
        
        # 处理"我"、"我的"
        if "我" in text or "我的" in text:
            if self.user_context and self.user_context.get('current_user'):
                current_user = self.user_context['current_user']
                entity.name = current_user.get('name')
                entity.employee_id = current_user.get('employee_id')
                entity.department = current_user.get('department')
                return entity
        
        # 匹配员工工号（E001格式）
        employee_id_match = re.search(r'\bE\d{3,}\b', text, re.IGNORECASE)
        if employee_id_match:
            entity.employee_id = employee_id_match.group(0).upper()
        
        # 匹配常见姓名（2-4个中文字符）
        name_match = re.search(r'[张李王刘陈杨黄赵吴周徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾肖田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦付方白邹孟熊秦邱江尹薛闫段雷侯龙史陶黎贺顾毛郝龚邵万钱严覃武戴莫孔向汤](?:[一二三四五六七八九十百千万亿兆零壹贰叁肆伍陆柒捌玖拾佰仟万亿兆]+|[a-zA-Z]+|[一-龥]{1,3})', text)
        if name_match and not entity.employee_id:
            # 简单匹配：常见姓氏 + 1-2个字的名字
            potential_name = name_match.group(0)
            if 2 <= len(potential_name) <= 4:
                entity.name = potential_name
        
        # 匹配部门（简单匹配）
        department_match = re.search(r'(.+?)(?:部|部门)', text)
        if department_match:
            entity.department = department_match.group(1) + "部"
        
        return entity
    
    def extract_all_entities(self, text: str) -> Dict[str, Any]:
        """
        提取所有实体
        
        Returns:
            包含所有提取实体的字典
        """
        return {
            "employee": self.extract_employee(text),
            "date_range": self.extract_date_range(text)
        }


class ParameterValidator:
    """参数验证和修正器"""
    
    def __init__(self, entity_extractor: EntityExtractor):
        """
        初始化参数验证器
        
        Args:
            entity_extractor: 实体提取器
        """
        self.entity_extractor = entity_extractor
    
    def validate_and_fix_params(
        self, 
        tool_name: str, 
        params: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        验证和修正工具参数
        
        Args:
            tool_name: 工具名称
            params: 原始参数
            context: 执行上下文
            
        Returns:
            修正后的参数
        """
        fixed_params = params.copy()
        context = context or {}
        
        # 根据工具类型进行参数修正
        if tool_name == "query_employee_info":
            # 如果提供了name但没有employee_id，保持name
            # 如果提供了employee_id，使用employee_id
            if "employee_id" in fixed_params and fixed_params["employee_id"]:
                # 验证employee_id格式
                emp_id = str(fixed_params["employee_id"]).strip().upper()
                if not emp_id.startswith("E"):
                    # 如果不是E开头，可能是姓名，交换
                    if "name" not in fixed_params or not fixed_params["name"]:
                        fixed_params["name"] = emp_id
                        del fixed_params["employee_id"]
                else:
                    fixed_params["employee_id"] = emp_id
        
        elif tool_name in ["query_reimbursement_summary", "query_reimbursement_records", "query_reimbursement_status"]:
            # 需要employee_id
            if "employee_id" not in fixed_params or not fixed_params["employee_id"]:
                # 尝试从context获取
                if "employee_id" in context:
                    fixed_params["employee_id"] = context["employee_id"]
                elif "name" in fixed_params:
                    # 有name但没有employee_id，需要先查询（这个在计划验证中处理）
                    pass
            
            # 处理日期参数
            if "start_date" in fixed_params and fixed_params["start_date"]:
                fixed_params["start_date"] = self._parse_date(fixed_params["start_date"])
            if "end_date" in fixed_params and fixed_params["end_date"]:
                fixed_params["end_date"] = self._parse_date(fixed_params["end_date"])
            
            # 如果提供了月份描述，转换为日期
            if "month" in str(fixed_params.get("start_date", "")) or "月" in str(fixed_params.get("start_date", "")):
                date_range = self.entity_extractor.extract_date_range(str(fixed_params.get("start_date", "")))
                if date_range.start_date:
                    fixed_params["start_date"] = date_range.start_date
                if date_range.end_date:
                    fixed_params["end_date"] = date_range.end_date
        
        elif tool_name == "create_work_order":
            # assignee_id需要验证
            if "assignee_id" in fixed_params:
                assignee_id = str(fixed_params["assignee_id"]).strip().upper()
                if assignee_id.startswith("E"):
                    fixed_params["assignee_id"] = assignee_id
                elif "assignee_id" in context:
                    fixed_params["assignee_id"] = context["assignee_id"]
        
        return fixed_params
    
    def _parse_date(self, date_str: str) -> str:
        """
        解析日期字符串为YYYY-MM-DD格式
        
        Args:
            date_str: 日期字符串
            
        Returns:
            YYYY-MM-DD格式的日期字符串
        """
        if not date_str:
            return date_str
        
        # 如果已经是YYYY-MM-DD格式
        if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
            return date_str
        
        # 尝试解析其他格式
        try:
            # 尝试常见格式
            for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y年%m月%d日']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        except Exception:
            pass
        
        # 如果无法解析，返回原字符串（让调用方处理）
        return date_str


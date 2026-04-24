#!/usr/bin/env python3
"""C30在线平台 API 自动化测试/执行脚本
基于逆向 chunk-85f99c46.js 的完整API文档
"""

import requests
import json
import time
import sys

BASE_URL = "https://pxservice.iclass30.com/gatewayApi"

class C30API:
    def __init__(self, username, password):
        self.token = None
        self.username = username
        self.password = password
        self.user_info = None
    
    def _headers(self):
        return {"token": self.token} if self.token else {}
    
    def _get(self, path, params=None):
        r = requests.get(f"{BASE_URL}{path}", headers=self._headers(), params=params)
        return r.json()
    
    def _post(self, path, data=None, as_form=False):
        headers = self._headers()
        if as_form:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            r = requests.post(f"{BASE_URL}{path}", headers=headers, data=data)
        else:
            headers["Content-Type"] = "application/json"
            r = requests.post(f"{BASE_URL}{path}", headers=headers, data=json.dumps(data) if data else None)
        return r.json()
    
    # ==================== 登录 ====================
    def login(self):
        """登录获取token"""
        r = self._get("/user/portal/newLoginApp", {
            "userName": self.username,
            "password": self.password,
            "clientId": 4,
            "sourceType": 4,
            "terminalType": "h5"
        })
        if r.get("code") == 200:
            self.token = r["result"]["token"]
            return True
        return False
    
    # ==================== 用户信息 ====================
    def get_my_info(self):
        """获取当前用户信息"""
        return self._get("/user/user/getMyInfo")
    
    # ==================== 签到 ====================
    def sign_get(self, face_teach_id):
        """🚨 获取签到详情(泄露签到码和坐标)"""
        return self._get("/faceteach/sign/get", {"faceTeachId": face_teach_id})
    
    def sign_participate(self, face_teach_id, sign_type, address, sign_data, plan_id=""):
        """执行签到/签退"""
        params = {
            "signType": sign_type,  # 0=签到, 1=签退
            "address": address,
            "signDay": "",
            "signData": json.dumps(sign_data),
            "planId": plan_id
        }
        return self._post("/faceteach/sign/study/participate", params)
    
    # ==================== 讨论 ====================
    def discuss_view(self, face_teach_id):
        """获取讨论详情"""
        return self._get("/faceteach/discuss/view", {"faceTeachId": face_teach_id})
    
    def discuss_reply_add(self, discuss_id, content, parent_id=""):
        """提交讨论回复"""
        params = {
            "discussId": discuss_id,
            "parentId": parent_id,
            "sourceType": 1,
            "url": "",
            "content": content,
            "file": "[]"
        }
        return self._post("/faceteach/discuss/reply/add", params)
    
    # ==================== 头脑风暴 ====================
    def brainstorm_add_stu(self, brainstorm_id, answer, face_teach_id):
        """提交头脑风暴观点"""
        params = {
            "brainstormId": brainstorm_id,
            "answer": answer,
            "faceTeachId": face_teach_id,
            "file": "[]"
        }
        return self._post("/faceteach/brainstormstu/addBrainStormStu", params)
    
    # ==================== 投票 ====================
    def vote_get(self, vote_id):
        """获取投票详情"""
        return self._get("/faceteach/vote/get", {"voteId": vote_id})
    
    def vote_participate(self, vote_id, selected_options):
        """提交投票 selected_options: 选项sortOrder列表如[1,3]"""
        params = {
            "voteId": vote_id,
            "content": ",".join(str(x) for x in selected_options)
        }
        return self._post("/faceteach/vote/study/participate", params)
    
    # ==================== 问卷 ====================
    def questionnaire_get_stu_ques(self, face_teach_id, questionnaire_id):
        """获取问卷题目"""
        return self._get("/faceteach/questionnaire/getQuestionStuQues", {
            "faceTeachId": face_teach_id,
            "questionnaireId": questionnaire_id,
            "sourceType": 4
        })
    
    def questionnaire_get_answer_info(self, face_teach_id, questionnaire_id, question_id):
        """🚨 获取问卷答案统计(可能泄露)"""
        return self._get("/faceteach/questionnaire/getQuestionAnswerInfo", {
            "faceTeachId": face_teach_id,
            "questionnaireId": questionnaire_id,
            "questionId": question_id
        })
    
    def questionnaire_save_answer(self, answer_data):
        """保存问卷答案"""
        return self._post("/faceteach/questionnaire/saveQuestionAnswer", answer_data)
    
    def questionnaire_save_stu_ques(self, submit_data):
        """提交完整问卷"""
        return self._post("/faceteach/questionnaire/saveQuestionStuQues", submit_data)
    
    # ==================== 课件/刷课 ====================
    def stu_cell_get_modules(self, open_course_id, course_id):
        """获取课程模块列表"""
        return self._get("/design/stuCell/getOpenCourseModuleByStu", {
            "openCourseId": open_course_id,
            "courseId": course_id
        })
    
    def stu_cell_preview(self, course_id, open_course_id, cell_id):
        """获取课件预览(含tokenId)"""
        return self._get("/design/stuCell/getCellPreviewByStu", {
            "courseId": course_id,
            "openCourseId": open_course_id,
            "cellId": cell_id
        })
    
    def study_save_progress(self, course_id, open_course_id, cell_id, token_id, 
                           study_time=30, video_max_time=0, study_max_page=1):
        """上报学习进度(刷课核心)"""
        params = {
            "courseId": course_id,
            "openCourseId": open_course_id,
            "cellId": cell_id,
            "studyTime": study_time,
            "studyVideoMaxTime": video_max_time,
            "studyMaxPage": study_max_page,
            "videoTimeTotalLong": "",
            "tokenId": token_id
        }
        return self._get("/design/study/saveStudyCellInfo", params)
    
    def auto_study_cell(self, course_id, open_course_id, cell_id, target_seconds=0):
        """自动刷课 - 循环上报学习进度直到完成"""
        preview = self.stu_cell_preview(course_id, open_course_id, cell_id)
        if preview.get("code") != 200:
            return preview
        
        token_id = preview["result"].get("tokenId", "")
        total_time = 0
        
        while True:
            r = self.study_save_progress(course_id, open_course_id, cell_id, token_id)
            total_time += 30
            print(f"  已学习 {total_time}秒...")
            
            # Check completion
            check = self.stu_cell_preview(course_id, open_course_id, cell_id)
            if check.get("code") == 200 and check["result"].get("cellProcess", 0) >= 100:
                print(f"  ✅ 课件学习完成!")
                break
            
            if target_seconds > 0 and total_time >= target_seconds:
                print(f"  达到目标时间 {target_seconds}秒")
                break
            
            time.sleep(1)  # 1秒间隔(原前端30秒)
        
        return {"status": "completed", "totalTime": total_time}
    
    # ==================== 评价 ====================
    def evaluation_stu_get(self, face_teach_id):
        """获取学生评价"""
        return self._get("/faceteach/evaluation/stu/get", {"faceTeachId": face_teach_id})
    
    def evaluation_stu_save(self, evaluation_data):
        """提交学生评价"""
        return self._post("/faceteach/evaluation/stu/save", evaluation_data)
    
    # ==================== 课堂码/加入 ====================
    def join_by_classroom_code(self, code):
        """通过6位课堂码加入课堂"""
        return self._post("/faceteach/activity/stu/involve", 
                          {"classroomCode": code}, as_form=False)
    
    def join_course_by_invite_code(self, invite_code, join_type=1):
        """通过邀请码加入班级/课程"""
        return self._post("/course/openCourse/joinCourseByStu", 
                          {"inviteCode": invite_code, "type": join_type}, as_form=False)
    
    def activity_involve(self, face_teach_id):
        """加入课堂活动"""
        return self._post("/faceteach/activity/stu/involve", 
                          {"faceTeachId": face_teach_id}, as_form=False)
    
    # ==================== PK/小组 ====================
    def pk_add_face_to_face(self, face_teach_id, group_pk_id, random_code):
        """面对面加入PK"""
        params = {
            "faceTeachId": face_teach_id,
            "groupPkId": group_pk_id,
            "randomCode": random_code
        }
        return self._post("/faceteach/pk/addFaceToFace", params, as_form=True)
    
    def pk_stu_join_group(self, open_course_id, homework_id, group_id):
        """学生加入PK小组"""
        params = {
            "openCourseId": open_course_id,
            "homeworkId": homework_id,
            "groupId": group_id
        }
        return self._post("/faceteach/pk/stuJoinGroup", params, as_form=True)
    
    # ==================== 作业/考试 ====================
    def workexam_get_by_id(self, workexam_id):
        """获取作业/考试详情"""
        return self._get("/workexam/workexam/getById", {"id": workexam_id})
    
    def workexam_get_paper_struct(self, workexam_id):
        """获取试卷结构"""
        return self._get("/workexam/workexam/getPaperStruct", {"workexamId": workexam_id})
    
    # ==================== 课程 ====================
    def stu_course_list(self, page=1, page_size=10):
        """获取学生课程列表"""
        return self._post("/course/stuCourse/getStuCourseList", 
                          {"page": page, "pageSize": page_size})
    
    def course_evaluate_get(self, open_course_id, course_id):
        """获取课程评价"""
        return self._get("/course/evaluate/getEvaluate", {
            "openCourseId": open_course_id,
            "courseId": course_id
        })
    
    def course_evaluate_save(self, evaluate_data):
        """保存课程评价"""
        return self._get("/course/evaluate/saveEvaluate", evaluate_data)

# ==================== 使用示例 ====================
if __name__ == "__main__":
    api = C30API("2504140523", "114114Aa@")
    
    if api.login():
        print(f"✅ 登录成功! Token: {api.token[:20]}...")
        
        info = api.get_my_info()
        if info.get("code") == 200:
            r = info["result"]
            print(f"  用户: {r.get('displayName')}")
            print(f"  学号: {r.get('employeeNumber')}")
            print(f"  学校: {r.get('schoolName')}")
    else:
        print("❌ 登录失败")

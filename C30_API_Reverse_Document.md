# C30在线平台 - 完整API逆向文档

> 逆向来源: chunk-85f99c46.564a8d01.js (3.1MB, 312个API端点)
> 网关地址: https://pxservice.iclass30.com/gatewayApi
> 认证方式: HTTP Header `token: <login_token>`

---

## 一、HTTP工具层架构

### 核心发现: s["a"] = GET, s["b"] = POST

JS中所有API通过模块 `"086a"` 提供的 `s["a"]`(GET) 和 `s["b"]`(POST) 方法封装：

```javascript
// GET调用: s["a"]("/gatewayApi/xxx", params)
// POST调用: s["b"]("/gatewayApi/xxx", JSON.stringify(data), "", contentType)

// contentType参数：
//   "" (默认) → Content-Type: application/json
//   "urlencoded" → Content-Type: application/x-www-form-urlencoded
//   "setScore" → 使用默认JSON但标记为评分操作
//   "participate" → 标记为参与操作
//   "involve" → 标记为加入课堂操作
//   "deleteActivity" → 标记为删除活动操作
//   "saveDisCussPraise" → 标记为讨论点赞
//   "setReplyType" → 修改回复类型
//   "updateState" → 更新状态
//   "saveQuestionStuQues" → 保存问卷学生答案
//   "markScore" → 评分标记
//   "continueAnswer" → 继续答题
//   "stuRedo" / "workExamredo" → 学生重做/作业重做
```

---

## 二、功能模块详细逆向

### 1. 讨论(discuss) - 8个API

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 讨论详情 | GET | `/faceteach/discuss/view` | 获取讨论详情 |
| 回复列表 | GET | `/faceteach/discuss/reply/list` | 获取回复分页列表 |
| 子回复列表 | GET | `/faceteach/discuss/reply/subList` | 获取子回复列表 |
| **添加回复** | **POST** | **`/faceteach/discuss/reply/add`** | **学生提交讨论回复** |
| 点赞回复 | POST | `/faceteach/discuss/reply/praise` | 点赞某条回复 |
| 更新讨论 | POST | `/faceteach/discuss/update` | 更新讨论内容 |
| 设置回复类型 | POST | `/faceteach/discuss/setReplyType` | 设置回复方式 |
| 设置评分 | POST | `/faceteach/discuss/setScore` | 教师评分 |

#### 🔑 自动提交讨论回复链路

**API**: `POST /gatewayApi/faceteach/discuss/reply/add`

**请求体** (JSON字符串):
```json
{
  "discussId": "讨论ID",
  "parentId": "父回复ID(顶级回复为0或空)",
  "sourceType": 1,
  "url": "",
  "content": "回复内容文本",
  "file": "[{\"md5\":\"\",\"title\":\"文件名\",\"requestLength\":0,\"url\":\"文件URL\",\"docType\":\"文件类型\"}]"  // 可选:附件JSON
}
```

**Vue源码** (`addDiscussReply`方法):
```javascript
addDiscussReply: function() {
  var fileList = [];
  this.fileList.forEach(function(t) {
    fileList.push({md5: t.md5, title: t.title, requestLength: t.size, url: t.docUrl, docType: t.type});
  });
  var params = {
    discussId: this.discussId,
    sourceType: 1,
    url: "",
    content: this.replyContent,
    parentId: this.parentId,
    file: JSON.stringify(fileList)
  };
  // Object(l["b"])(JSON.stringify(params)) → POST /discuss/reply/add
}
```

**自动提交可行性**: ✅ **完全可行** - 只需要 `discussId` + `content` 即可提交回复

---

### 2. 头脑风暴(brainstorm) - 5个API

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 获取详情 | GET | `/faceteach/brainstorm/getBrainStorm` | 获取头脑风暴详情 |
| 获取列表 | GET | `/faceteach/brainstorm/getBrainStormList` | 获取头脑风暴列表 |
| 创建/更新 | POST | `/faceteach/brainstorm/addOrUpdateBrainStorm` | 教师创建/更新头脑风暴 |
| **学生提交观点** | **POST** | **`/faceteach/brainstormstu/addBrainStormStu`** | **学生提交观点** |
| 更新学生评分 | POST | `/faceteach/brainstormstu/updateStuScore` | 教师评分学生观点 |

#### 🔑 自动提交头脑风暴观点链路

**API**: `POST /gatewayApi/faceteach/brainstormstu/addBrainStormStu`

**请求体** (JSON字符串):
```json
{
  "brainstormId": "头脑风暴ID",
  "answer": "观点内容",
  "faceTeachId": "课堂活动ID",
  "file": "[{\"md5\":\"\",\"title\":\"文件名\",\"requestLength\":0,\"url\":\"文件URL\",\"docType\":\"类型\"}]"  // 可选
}
```

**Vue源码** (`addBrainStormStu`方法):
```javascript
addBrainStormStu: function() {
  var fileList = [];
  this.fileList.forEach(function(t) {
    fileList.push({md5: t.md5, title: t.title, requestLength: t.size, url: t.docUrl, docType: t.type});
  });
  var params = {
    brainstormId: this.brainstormId,
    answer: this.replyContent,
    faceTeachId: this.activityId,
    file: JSON.stringify(fileList)
  };
  // Object(l["a"])(JSON.stringify(params)) → POST /brainstormstu/addBrainStormStu
}
```

**自动提交可行性**: ✅ **完全可行** - 只需要 `brainstormId` + `answer` + `faceTeachId`

---

### 3. 投票(vote) - 5个API

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 获取投票详情 | GET | `/faceteach/vote/get` | 获取投票数据(含选项) |
| 投票结果数据 | GET | `/faceteach/vote/study/getStudyData` | 获取投票统计结果 |
| 投票列表 | GET | `/faceteach/vote/study/list` | 获取投票列表 |
| **学生投票参与** | **POST** | **`/faceteach/vote/study/participate`** | **学生提交投票** |
| 创建投票 | POST | `/faceteach/vote/add` | 教师创建投票 |

#### 🔑 自动投票链路

**投票类型枚举** (voteType):
- `1` = 正确错误(单选)
- `2` = 赞成反对(单选) 
- `3` = 单选
- `4` = 多选(需selectMultipleCount参数)

**获取投票API**: `GET /gatewayApi/faceteach/vote/get?voteId=xxx`
- 返回: `voteType`, `optionData`(选项JSON), `selectMultipleCount`(多选最多数), `activityState`等

**投票参与API**: `POST /gatewayApi/faceteach/vote/study/participate`

**请求体**:
```json
{
  "voteId": "投票ID",
  "content": "1,3"  // 选中选项的sortOrder值，逗号分隔
}
```

**Vue源码** (`saveVote`方法):
```javascript
saveVote: function() {
  if (this.selectResult.length > 0) {
    var content = this.selectResult.join(",");
    var params = {voteId: this.voteId, content: content};
    // Object(h["G"])(params) → POST /vote/study/participate (contentType: "participate")
  }
}

// toggle选择逻辑:
// 单选(1,2,3): this.selectResult = [sortOrder]
// 多选(4): 添加到this.selectResult, 最多selectMultipleCount个
```

**⚠️ 答案泄露分析**: 
- `GET /vote/get?voteId=xxx` 返回选项数据但不直接泄露正确答案
- 投票活动没有"正确答案"概念(非考试，是投票统计)
- **无答案泄露漏洞**

**自动投票可行性**: ✅ **完全可行** - `voteId` + `content`(选项sortOrder) 即可

---

### 4. 问卷(questionnaire) - 12个API

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 学生获取题目 | GET | `/faceteach/questionnaire/getQuestionStuQues` | 学生获取问卷题目 |
| **保存单题答案** | **POST** | **`/faceteach/questionnaire/saveQuestionAnswer`** | **保存单个答案** |
| **提交整个问卷** | **POST** | **`/faceteach/questionnaire/saveQuestionStuQues`** | **学生提交完整问卷** |
| 获取答案统计 | GET | `/faceteach/questionnaire/getQuestionAnswerInfo` | 🚨获取单题答案统计(可能泄露) |
| 问卷详情(教师) | GET | `/faceteach/questionnaire/getQuestionnaireInfo` | 教师获取完整问卷信息 |
| 编辑问卷 | GET | `/faceteach/questionnaire/editQuestionnaire` | 获取可编辑的问卷 |
| 保存/开始问卷 | GET | `/faceteach/questionnaire/save` | 保存活动 |
| 添加题目 | POST | `/faceteach/questionnaireQues/saveQuestionInfo?<params>` | 添加/编辑题目 |
| 删除题目 | POST | `/faceteach/questionnaireQues/deleteQuestion` | 删除题目 |
| 从题库导入 | GET | `/faceteach/questionnaireQues/importFromQuesBank` | 从题库导入 |
| 题目列表 | GET | `/faceteach/questionnaire/ques/list` | 获取题目列表 |
| 题目详情 | GET | `/faceteach//questionnaire/ques/info` | 单题详情(注意双斜杠) |

#### 🔑 自动填写提交问卷链路

**步骤1 - 获取问卷题目**:
```
GET /faceteach/questionnaire/getQuestionStuQues?faceTeachId=xxx&questionnaireId=xxx&sourceType=4
```
返回:
```json
{
  "result": {
    "title": "问卷标题",
    "dataDTOList": [...],  // 题目列表
    "questionnaireStuId": "学生问卷ID",
    "isAnswer": true,    // 是否已答
    "state": 2           // 问卷状态
  }
}
```

**题目类型枚举** (questionType):
- `1` = 单选
- `2` = 多选  
- `3` = 正确错误
- `4` = 赞成反对
- `5` = 问答题

**步骤2 - 保存单题答案**:
```
POST /faceteach/questionnaire/saveQuestionAnswer
Body: JSON字符串，包含答案数据
```

**步骤3 - 提交整个问卷**:
```
POST /faceteach/questionnaire/saveQuestionStuQues
contentType: "saveQuestionStuQues"
Body: JSON字符串，包含questionnaireStuId等
```

#### 🚨 答案泄露漏洞分析

**关键API**: `GET /faceteach/questionnaire/getQuestionAnswerInfo`

此API设计用于课堂投屏场景，教师展示各选项的投票/问卷统计结果。**参数为**:
```
?faceTeachId=xxx&questionnaireId=xxx&questionId=xxx
```

**返回数据**:
```json
{
  "result": [
    {
      "sortOrder": 0,
      "content": "选项内容",
      "stuCount": 5,   // 选择此选项的人数
      "stuCount1": "5"
    }
  ]
}
```

**漏洞判定**: ⚠️ **部分泄露** - 此接口返回每个选项的选择人数统计，不直接返回"正确答案"。但对于单选/对错题目，根据stuCount分布可以推测正确答案。需要**活动进行中**才能获取统计。

**自动问卷可行性**: ✅ **可行** - 获取题目 → 构造答案 → 提交

---

### 5. 课件/资源(cell/courseware/study) - 22个API

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 学生课程模块 | GET | `/design/stuCell/getOpenCourseModuleByStu` | 获取课程章节/模块 |
| 学生课件列表 | GET | `/design/stuCell/getCellListByStu` | 获取课件列表 |
| **课件预览** | **GET** | **`/design/stuCell/getCellPreviewByStu`** | **获取课件详情+学习进度** |
| **保存学习进度** | **GET** | **`/design/study/saveStudyCellInfo`** | **上报学习时间(刷课核心)** |
| 课件详情(教师) | GET | `/design/cell/getCellInfoById` | 教师获取课件详情 |
| 课件预览(教师) | GET | `/design/cell/getCellPreview` | 教师课件预览 |
| 课件列表(教师) | GET | `/design/cell/getCellListByLevel` | 按层级获取列表 |
| 视频剪辑 | GET | `/design/cell/getVideoClipByCellId` | 获取视频剪辑 |
| 添加课件 | POST | `/design/cell/addCellByCourseDoc` | 添加课件 |
| 添加测验 | POST | `/design/cell/addCellTest` | 添加课件测验 |
| 添加本地文档 | POST | `/design/cell/addLocalDocList` | 添加本地文档 |
| 删除课件 | GET | `/design/cell/delCell` | 删除课件 |
| 编辑课件名 | POST | `/design/cell/editCellName?params` | 编辑课件名称 |
| 编辑课件节点 | POST | `/design/cell/editCellNode` | 编辑课件节点 |
| 排序保存 | POST | `/design/cell/saveCellDataBySort?params` | 保存排序 |
| 设置下载 | GET | `/design/cell/setIsDownload` | 设置是否可下载 |
| 课堂课件预览 | GET | `/faceteach/cell/getFaceTeachCellPreview` | 课堂课件预览 |
| 获取课堂课件ID | GET | `/faceteach/cell/getIdByFaceTeachCell` | 获取课堂课件ID |
| 保存课堂课件列表 | POST | `/faceteach/cell/saveFaceTeachCellList` | 保存课堂课件 |
| 学生课件预览 | GET | `/faceteach/cell/stu/preview` | 学生课件预览 |
| 课件题目列表 | GET | `/design/cellQuestion/getCellQuestionList` | 获取课件题目 |
| 课件题目详情 | GET | `/design/cellQuestion/getQuestion` | 获取题目详情 |
| 保存课件题目答案 | GET | `/design/cellQuestion/saveStuCellQuestion` | 保存课件题目答案 |

#### 🔑 自动刷课链路

**步骤1 - 获取课件预览(获取tokenId)**:
```
GET /design/stuCell/getCellPreviewByStu?courseId=xxx&openCourseId=xxx&cellId=xxx&upModuleId=
```
返回关键字段:
```json
{
  "result": {
    "tokenId": "学习凭证ID",
    "cellName": "课件名",
    "studyMaxTime": 0,     // 最大学习时间
    "cellProcess": 0,      // 学习进度(0-100,100=完成)
    "isAllowDrag": 0,      // 是否允许拖拽
    "isDoubleSpeed": 0,    // 是否允许倍速
    "preview": {...},      // 课件资源
    "category": "video/mp3/..."  // 资源类型
  }
}
```

**步骤2 - 循环上报学习进度(每30秒一次)**:
```
GET /design/study/saveStudyCellInfo
```
参数:
```json
{
  "courseId": "课程ID",
  "openCourseId": "开课ID",
  "cellId": "课件ID",
  "studyTime": 30,           // 每次上报30秒
  "studyVideoMaxTime": 0,    // 视频最大播放时间
  "studyMaxPage": 1,         // PDF最大阅读页数
  "videoTimeTotalLong": "",  // 视频总时长
  "tokenId": "从预览获取的tokenId"
}
```

**Vue源码** (`saveStudyCellInfo`方法):
```javascript
saveStudyCellInfo: function() {
  if (this.cellId) {
    if (5 == this.typeShow && this.$refs["updateMaxTime"]) {
      this.videoMaxTime = this.$refs["updateMaxTime"].getMaxTime();
    }
    var params = {
      courseId: this.courseId,
      openCourseId: this.openCourseId,
      cellId: this.cellId,
      studyTime: 30,  // 固定上报30秒
      studyVideoMaxTime: this.videoMaxTime,
      studyMaxPage: this.studyMaxPage,
      videoTimeTotalLong: "",
      tokenId: this.tokenId
    };
    // GET /design/study/saveStudyCellInfo
  }
}
```

**自动刷课可行性**: ✅ **完全可行** - 核心是获取tokenId后循环调用saveStudyCellInfo
- **注意**: saveStudyCellInfo虽然是GET请求，但实际会更新服务器端学习进度
- 每次上报studyTime=30秒，循环调用即可刷课
- cellProcess达到100时表示完成

---

### 6. 作业/考试(workexam) - 41个API

#### 核心API

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 学生作业课程列表 | GET | `/workexam/workexamStu/stuWorkCourseList` | 获取学生作业/考试列表 |
| 学生未答作业 | GET | `/workexam/workexamStu/stuNoAnswerWorkList` | 获取未答作业 |
| 学生课堂作业 | GET | `/workexam/workexamStu/getStuFaceWorkList` | 获取课堂作业 |
| 获取试卷结构 | GET | `/workexam/workexam/getPaperStruct` | 🚨获取试卷结构 |
| 预览试卷 | GET | `/workexam/paper/preview` | 预览试卷 |
| **开始答题** | **GET** | **`/workexam/workexam/getById`** | **获取题目(开始考试)** |
| **提交考试** | **POST** | **`/workexam/paper/mark/redo`** | **提交/重做考试** |
| 小组作业 | GET | `/workexam/group/stu/getGroupList` | 获取作业小组列表 |
| 小组学生列表 | GET | `/workexam/group/stu/getGroupStuList` | 获取小组学生 |
| 学生小组列表 | GET | `/workexam/group/stu/getStuGroupList` | 获取学生分组 |
| 加入作业小组 | POST | 通过`getStuGroupList`相关组件 | 加入小组 |
| 小组统计 | GET | `/workexam/group/getGroupStatistic` | 小组统计数据 |
| 小组评分 | POST | `/workexam/group/markGroupQuestion` | 小组评分 |
| 批量评分 | GET | `/workexam/group/markAllStu` | 批量评分 |
| 评分试卷 | POST | `/workexam/paper/mark/paper` | 评分试卷 |
| 评分题目 | POST | `/workexam/paper/mark/question` | 评分单个题目 |
| 评分子题 | POST | `/workexam/paper/mark/question/sub` | 评分子题 |
| 继续答题 | POST | `/workexam/paper/mark/continueAnswer` | 继续答题 |
| 删除批改文件 | POST | `/workexam/paper/mark/delMarkFile` | 删除批改文件 |
| 评分备注 | POST | `/workexam/paper/mark/markRemark` | 评分备注 |
| 重做(学生) | POST | `/workexam/paper/mark/redo` (stuRedo) | 学生重做 |
| 重做(教师) | POST | `/workexam/paper/mark/redo` (workExamredo) | 教师重新布置 |
| 保存批改文件 | POST | `/workexam/paper/mark/saveMarkFile` | 保存批改文件 |
| 学生查看批改 | GET | `/workexam/workexamStu/getMarkPaperByStu` | 学生查看批改结果 |
| 学生互评列表 | GET | `/workexam/workexamStu/getMutualListByStu` | 互评列表 |
| 学生互评详情 | GET | `/workexam/workexamStu/getMutualStuInfo` | 互评详情 |
| 题目评分(小组) | GET | `/workexam/workexamStu/getQuesGradeByGroup` | 小组题目评分 |
| 答题笔记(小组) | GET | `/workexam/workexamStu/getAnswerNotesByGroup` | 小组答题笔记 |
| 答题笔记(批改) | GET | `/workexam/workexamStu/getAnswerNotesByMark` | 批改答题笔记 |
| 保存学生评分 | GET | `/workexam/workexamStu/saveScore` | 保存学生成绩 |
| 题库列表 | GET | `/workexam/question/getList` | 获取题库列表 |
| 题目预览 | GET | `/workexam/question/previwQues` | 预览题目 |
| 发布考试 | GET | `/workexam/openClass/publishExaminfo` | 发布考试 |
| 发布到班级 | GET | `/workexam/openClass/publistForClass` | 发布到班级 |
| 获取班级 | GET | `/workexam/openClass/getClassByOpenCourseId` | 获取班级信息 |
| 作业详情 | GET | `/workexam/workexam/getById` | 获取作业/考试详情 |
| 课堂作业列表 | GET | `/workexam/workexam/getFaceWorkList` | 获取课堂作业 |
| 学生列表 | GET | `/workexam/workexam/getWorkexamStuList` | 获取学生列表 |
| 录制学生列表 | GET | `/workexam/workexam/getRecordingStuList` | 获取录制学生 |
| 保存作业消息 | GET | `/workexam/workexam/saveWorkMessage` | 保存作业消息 |
| 教师提交 | GET | `/workexam/workexam/submitByTea` | 教师提交 |
| 更新代码 | GET | `/workexam/workexam/updateCode` | 更新代码 |
| 作业课程列表 | GET | `/workexam/workexam/workCourseList` | 作业课程列表 |
| 审批作业列表 | GET | `/workexam/workexam/approvedWorkList` | 审批作业列表 |
| 教师清除 | GET | `/workexam/workexam/clearByTea` | 教师清空 |

#### 🔑 自动答题链路

**步骤1 - 开始考试/答题**:
```
POST /workexam/workexamStu/doAnswer  (从submitQuestion源码推断)
```
或通过课堂页面触发:
```javascript
// doAnswer方法
var i = {
  workexamId: this.examId,
  openCourseId: this.openCourseId,
  dataSource: 4,      // 4=H5, 2/3=APP
  workexamType: 2,    // 2=考试
  examWays: 1         // 1=在线
};
// 返回: data.result 包含题目列表、试卷信息等
```

**步骤2 - 提交考试**:
```javascript
// submitQuestion方法
var params = {
  paperTitle: this.data.paperTitle,
  stuAnswerJson: JSON.stringify(this.localList),  // 答案JSON
  newTokenId: this.newTokenId,
  dataSource: 4,
  workexamStuId: this.workexamStuId,
  useTime: this.useTime  // 用时(秒)
};
// POST /workexam/workexam/submit (通过v["M"]调用)
```

**stuAnswerJson结构** (推断):
```json
[
  {
    "workexamQuesId": "题目ID",
    "stuAnswer": "A"  // 或 "A,C" 多选，或文本
  }
]
```

#### 🚨 答案泄露漏洞分析

- `GET /workexam/workexam/getPaperStruct` - 获取试卷结构，可能泄露题目信息
- `GET /workexam/workexam/getById` - 获取作业详情，含题目
- **未发现直接的答案泄露接口**（sign/get式漏洞），但试卷结构API值得关注

**自动答题可行性**: ⚠️ **可行但复杂** - 需要先获取题目，构造答案再提交

---

### 7. 课程学习(study/stuCell) - 3个API

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 课程模块列表 | GET | `/design/stuCell/getOpenCourseModuleByStu` | 获取课程章节列表 |
| 课件列表 | GET | `/design/stuCell/getCellListByStu` | 获取课件列表 |
| 课件预览 | GET | `/design/stuCell/getCellPreviewByStu` | 获取课件详情+tokenId |
| **保存学习进度** | **GET** | **`/design/study/saveStudyCellInfo`** | **上报学习进度(核心)** |

(详细见第5节 课件/资源)

**自动刷课完整流程**:
1. `getOpenCourseModuleByStu` → 获取所有模块
2. 遍历模块的cellList → 获取每个cellId
3. `getCellPreviewByStu` → 获取tokenId和当前进度cellProcess
4. 如果cellProcess < 100，循环调用 `saveStudyCellInfo` (每30秒studyTime=30)
5. 直到cellProcess=100，转下一个课件

---

### 8. 评价(evaluation) - 4个API

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 评价列表 | GET | `/faceteach/evaluation/list` | 获取评价列表 |
| 教师评分 | POST | `/faceteach/evaluation/score` | 教师评分(contentType:setScore) |
| **学生获取评价** | **GET** | **`/faceteach/evaluation/stu/get`** | **学生获取评价项** |
| **学生提交评价** | **POST** | **`/faceteach/evaluation/stu/save`** | **学生提交评价** |

#### 🔑 自动评价链路

**PK组内/组间评价**（更复杂的评价，通过saveEvaluateContent）:
```javascript
// saveEvaluateContent方法 (组间互评示例)
var params = Object.assign({
  id: this.selectedItem.id || "",
  faceTeachId: this.$route.params.faceTeachId,
  groupPkId: this.$route.params.activityId,
  userId: this.selectedItem.creatorId,
  groupId: this.selectedItem.groupId
}, evaluationData);
// POST /faceteach/pk/saveEvaluateContent
```

**简单评分API**: `POST /faceteach/evaluation/stu/save`

**setScore评分**:
```javascript
setScore: function() {
  var params = {
    faceTeachId: this.faceTeachId,
    type: 1,
    stuId: this.stuInfo.stuId,
    score: this.score
  };
  // POST /faceteach/evaluation/score
}
```

**自动评价可行性**: ✅ **可行** - 需要faceTeachId + 评价数据

---

### 9. 课堂码/加入课堂(classCode/involve) - 3个API

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| **加入课堂(课堂码)** | **POST** | **课堂码组件内部** | **输入6位课堂码加入** |
| **加入班级(邀请码)** | **POST** | **`/course/openCourse/joinCourseByStu`** | **邀请码加入班级** |
| 加入课堂活动 | POST | `/faceteach/activity/stu/involve` | 加入课堂(involve) |

#### 🔑 自动加入课堂链路

**课堂码加入** (classCode组件):
```javascript
confirm: function() {
  var params = {classroomCode: this.value};
  // 验证: classroomCode必须是6位
  if (this.value && 6 == this.value.length) {
    // POST API调用(Object(y["k"]))
    // 成功后跳转到课堂活动页面
  }
}
```
返回: `{id, courseId, openCourseId}` → 即faceTeachId和课程信息

**邀请码加入班级**:
```javascript
joinCourseByStu: function() {
  var params = {inviteCode: this.addCode, type: 1};
  // POST /course/openCourse/joinCourseByStu
  // 返回0=直接加入成功, 非0=等待教师审核
}
```

**扫码加入**:
```javascript
scanJoinClass: function() {
  var params = {inviteCode: code, type: 0};  // type=0=扫码
  // POST /course/openCourse/joinCourseByStu
}
```

**加入课堂活动(involve)**:
```
POST /faceteach/activity/stu/involve
Body: JSON {"faceTeachId": "课堂ID"}
contentType: "involve"
```

**自动加入可行性**: ✅ **完全可行** - 只需6位课堂码或邀请码

---

### 10. PK/小组(group) - 35个API

#### PK核心API

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| PK列表(教师) | GET | `/faceteach/pk/getGroupPk` | 获取PK分组信息 |
| PK列表(学生) | GET | `/faceteach/pk/getGroupPkByStu` | 学生获取PK信息 |
| PK编辑 | GET | `/faceteach/pk/edit` | 编辑PK |
| 小组列表 | GET | `/faceteach/pk/getGroupList` | 获取小组列表 |
| **面对面加码** | **POST** | **`/faceteach/pk/addFaceToFace`** | **输入随机码加入PK** |
| **随机码加入小组** | **POST** | **`/faceteach/pk/addGroupByRandomCode`** | **按随机码加入小组** |
| **学生加入小组** | **POST** | **`/faceteach/pk/stuJoinGroup`** | **学生选择加入小组** |
| 退出小组 | GET | `/faceteach/pk/stu/exitGroup` | 退出小组 |
| 评价内容 | GET | `/faceteach/pk/getEvaluateContent` | 获取评价内容 |
| **保存评价内容** | **POST** | **`/faceteach/pk/saveEvaluateContent`** | **提交评价** |
| 学生评价统计 | GET | `/faceteach/pk/getStuEvaluateStatistic` | 评价统计 |
| 学生评价详情 | GET | `/faceteach/pk/getStuEvaluateDetail` | 评价详情 |
| 学生评价内容 | GET | `/faceteach/pk/getStuEvaluateContent` | 评价内容 |
| 学生评价方式 | GET | `/faceteach/pk/getStuWayEvaluate` | 获取可评价列表 |
| 教师小组评价 | GET | `/faceteach/pk/getTeaGroupEvaluate` | 教师小组评价 |
| 团队评价 | GET | `/faceteach/pk/getTeamEvaluate` | 团队评价 |
| PK评价设置 | GET | `/faceteach/pk/getPkEvaluate` | 获取评价配置 |
| 编辑PK评价 | POST | `/faceteach/pk/editPkEvaluate` | 编辑评价配置 |
| 评论回看 | GET | `/faceteach/pk/backStuComment` | 回看评论 |
| 保存学生评论 | POST | `/faceteach/pk/saveStuComment` | 保存评论(urlencoded) |
| 公共日志 | GET | `/faceteach/pk/getCommonLog` | 操作日志 |

#### 小组管理API

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 添加小组 | GET | `/faceteach/pk/group/addGroup` | 添加小组 |
| 删除小组 | GET | `/faceteach/pk/group/removeGroup` | 删除小组 |
| 编辑组名 | GET | `/faceteach/pk/group/editGroupName` | 编辑小组名称 |
| 设置小组分数 | GET | `/faceteach/pk/group/setScore` | 设置小组分数 |
| 清空分数 | GET | `/faceteach/pk/group/clearScore` | 清空小组分数 |

#### 小组成员API

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 添加学生 | POST | `/faceteach/pk/stu/addStu?<params>` | 添加学生到小组 |
| 移除学生 | POST | `/faceteach/pk/stu/removeStu?<params>` | 从小组移除学生 |
| 未分组学生 | GET | `/faceteach/pk/stu/getNotGroupStuList` | 获取未分组学生 |
| 已分组学生 | GET | `/faceteach/pk/stu/getGroupStuList` | 获取组内学生 |
| 所有组学生 | GET | `/faceteach/pk/stu/getAllGroupStuList` | 所有分组学生 |
| 一键分组 | GET | `/faceteach/pk/stu/oneKeyGrouping` | 自动随机分组 |
| 引用班级分组 | GET | `/faceteach/pk/stu/quoteClassGroup` | 引用班级分组 |
| 设置组长 | GET | `/faceteach/pk/saveGroupLeader` | 设置组长 |
| 设置学生总分 | GET | `/faceteach/pk/setStuTotalScore` | 设置总分 |

#### 🔑 学生加入小组链路

**面对面加码(PK签到)**:
```javascript
addFaceToFace: function() {
  var params = {
    faceTeachId: this.$route.params.faceTeachId,
    groupPkId: this.$route.params.activityId,
    randomCode: this.aCheckCodeInput.join("")  // 输入的随机码
  };
  // POST /faceteach/pk/addFaceToFace (urlencoded)
}
```

**随机码加入小组**:
```javascript
addGroupByRandomCode: function() {
  var params = {
    faceTeachId: this.$route.params.faceTeachId,
    groupPkId: this.$route.params.activityId,
    randomCode: this.aCheckCodeInput.join("")
  };
  // POST /faceteach/pk/addGroupByRandomCode (urlencoded)
}
```

**学生选择加入小组**:
```javascript
// 点击小组 → 确认加入
stuJoinGroup: function() {
  // POST /faceteach/pk/stuJoinGroup (urlencoded)
  // 参数: {openCourseId, homeworkId, groupId}
}
```

---

### 11. 签到(sign) - 9个API

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 🚨**获取签到详情** | **GET** | **`/faceteach/sign/get`** | **🚨泄露签到验证码/坐标** |
| 签到统计 | GET | `/faceteach/sign/stats/get` | 签到统计 |
| 学生签到列表 | GET | `/faceteach/sign/study/list` | 学生签到列表 |
| 签到数据 | GET | `/faceteach/sign/study/getStudyData` | 获取签到数据 |
| **执行签到** | **POST** | **`/faceteach/sign/study/participate`** | **学生签到/签退** |
| 更新状态 | POST | `/faceteach/sign/study/updateState` | 更新签到状态 |
| 更新表现评分 | POST | `/faceteach/sign/study/updatePerformanceScore` | 更新表现评分 |
| 创建签到 | POST | `/faceteach/sign/add` | 教师创建签到 |
| 更新签到码 | GET | `/faceteach/sign/updateSignCodeById` | 更新签到码 |

#### 🚨🚨 签到答案泄露漏洞 (sign/get)

**已知漏洞**: `GET /faceteach/sign/get?faceTeachId=xxx`

此API返回签到详情，包含:
```json
{
  "result": {
    "signCode": "123456",     // 🚨签到验证码(明文)!
    "signType": 0,            // 0=签到, 1=签退
    "longitude": "113.xxx",   // 🚨签到坐标经度
    "latitude": "34.xxx",     // 🚨签到坐标纬度
    "address": "xxx路xxx号",   // 🚨签到地址
    "state": 2               // 签到状态
  }
}
```

**漏洞利用**: 学生可以先调用sign/get获取验证码和坐标，再调用participate完成签到

#### 🔑 自动签到链路

```javascript
participate: function(address, signData) {
  var params = {
    signType: this.signType,       // 0=签到, 1=签退
    address: address,              // 地址(从地图获取)
    signDay: this.notToday ? this.displayDate : "",
    signData: JSON.stringify(signData),  // 签到数据(地图截图?)
    planId: this.planId
  };
  // POST /faceteach/sign/study/participate (contentType: "participate")
}
```

---

### 12. 活动(activity) - 10个API

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 活动列表(教师) | GET | `/faceteach/activity/list` | 教师获取活动列表 |
| 活动列表(学生) | GET | `/faceteach/activity/stu/list` | 学生获取活动列表 |
| **加入课堂** | **POST** | **`/faceteach/activity/stu/involve`** | **学生加入课堂** |
| 课堂详情 | GET | `/faceteach/activity/stu/getFaceClassroomInfo` | 获取课堂详情 |
| 参与统计 | GET | `/faceteach/activity/partInStat` | 参与统计 |
| 设置状态 | POST | `/faceteach/activity/setState` | 开启/关闭活动 |
| 删除活动 | POST | `/faceteach/activity/delete` | 删除活动 |
| 额外评分 | GET | `/faceteach/activity/saveStuExtraScore` | 保存学生额外分 |
| 导入活动 | GET | `/faceteach/activity/getImportActivities` | 获取可导入活动 |
| 执行导入 | POST | `/faceteach/activity/importActivities` | 导入活动 |

---

### 13. 测验(quiz) - 8个API

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 获取测验信息 | GET | `/faceteach/quiz/getFaceQuizInfo` | 获取测验详情 |
| 学生测验信息 | GET | `/faceteach/quizStu/getQuizStuInfo` | 学生获取测验 |
| **抢答** | **GET** | **`/faceteach/quizStu/rushToAnswer`** | **学生抢答** |
| 学生列表 | GET | `/faceteach/quiz/getQuizStuList` | 获取答题学生 |
| 课程测验列表 | GET | `/faceteach/quiz/getCourseQuizStuList` | 课程测验列表 |
| 摇一摇学生 | GET | `/faceteach/quiz/getShakeStu` | 随机选人 |
| 保存测验分数 | POST | `/faceteach/quiz/saveStuQuizScore` | 保存分数(setScore) |
| 更新测验 | POST | `/faceteach/quiz/update` | 更新测验 |

---

## 三、其他重要模块

### 14. 用户(user) - 8个API

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| **登录** | **GET** | **`/user/portal/newLoginApp`** | **登录获取token** |
| 职教云登录 | GET | `/user/portal/zjyLogin` | 职教云登录 |
| 获取我的信息 | GET | `/user/user/getMyInfo` | 获取用户详情 |
| 获取用户信息 | GET | `/user/user/getUserInfo` | 获取用户信息 |
| 教师科目列表 | GET | `/user/user/getTeaSubList` | 教师科目 |
| 教师列表 | GET | `/user/user/getUserListByFaceteacher` | 课堂教师列表 |
| 修改密码 | POST | `/user/user/student/revisePwd` | 学生修改密码(urlencoded) |
| 申请人信息 | GET | `/user/applicants/getApplicantsInfo` | 申请人信息 |
| 编辑申请人 | POST | `/user/applicants/editApplicants` | 编辑申请人 |
| 申请人岗位 | GET | `/user/applicants/getApplicantsPost` | 申请人岗位 |

**登录参数**:
```
GET /user/portal/newLoginApp?userName=学号&password=密码&clientId=4&sourceType=4&terminalType=h5
```

---

### 15. 课程(course) - 57个API (最大模块)

关键学生端API:

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 学生课程列表 | GET(POST) | `/course/stuCourse/getStuCourseList` | 获取学生课程 |
| 课程首页数据 | GET | `/course/stuCourse/getStuCourseHomeInfo` | 今日课堂数据 |
| **加入课程** | **GET** | **`/course/openCourse/joinCourseByStu`** | **邀请码加入课程** |
| 加入学习 | GET | `/course/courseStu/joinStudy` | 加入学习 |
| 获取学生状态 | GET | `/course/gateway/getStuState` | 获取学习状态 |
| 课程评价获取 | GET | `/course/evaluate/getEvaluate` | 获取课程评价 |
| 课程评价列表 | GET | `/course/evaluate/getEvaluateList` | 评价列表 |
| **保存课程评价** | **GET** | **`/course/evaluate/saveEvaluate`** | **提交课程评价** |
| 公告列表 | GET | `/course/announcement/getList` | 公告列表 |
| 公告详情 | GET | `/course/announcement/viewDetail` | 公告详情 |

---

### 16. 讨论(BBS/互动) - 23个API

课程内互动讨论模块:

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 互动列表 | GET | `/design/bbs/getCellInteractList` | 获取互动列表 |
| **添加互动** | **POST** | **`/design/bbs/addCellInteract`** | **发布互动讨论** |
| **添加回复** | **POST** | **`/design/bbs/addInteractReply`** | **回复互动** |
| 编辑互动 | POST | `/design/bbs/editCellInteract` | 编辑互动(urlencoded) |
| 编辑回复 | POST | `/design/bbs/editInteractReply` | 编辑回复(urlencoded) |
| 点赞 | POST | `/design/bbs/praise` | 点赞 |
| 回复列表 | GET | `/design/bbs/getReplyListById` | 回复列表 |
| 删除互动 | GET | `/design/bbs/deleteCellInteract` | 删除互动 |
| 话题列表 | GET | `/design/bbs/getTopicList` | 话题列表 |
| 话题信息 | GET | `/design/bbs/getTopicInfoByCell` | 话题详情 |
| 添加话题数据 | POST | `/design/bbs/addTopicData` | 添加话题数据(urlencoded) |
| 保存BBS评分 | GET | `/design/bbs/saveBBsScore` | 保存BBS评分 |
| 设置 | GET | `/design/bbs/getBbsSetUp` | 获取设置 |
| 保存设置 | POST | `/design/bbs/setBbsSetUp` | 保存设置(urlencoded) |
| 编辑话题 | POST | `/design/bbsTopic/editBBsTopic` | 编辑话题(urlencoded) |
| 删除话题 | GET | `/design/bbsTopic/delBBsTopic` | 删除话题 |
| 回复列表(备选) | GET | `/design/bbs/listReplyById` | 回复列表 |

**添加互动讨论参数**:
```javascript
addCellInteract: function() {
  var params = {
    cellId: this.info.cellId,
    content: this.formatWord(this.message),
    courseId: this.courseId,
    openCourseId: this.openCourseId,
    docJson: "",
    fromPlat: 1,
    interactType: this.type,
    star: this.star
  };
  // POST /design/bbs/addCellInteract
}
```

**添加回复参数**:
```javascript
addInteractReply: function() {
  var params = {
    courseId: this.courseId,
    openCourseId: this.openCourseId,
    cellId: this.cellId,
    resId: this.resId,
    resType: this.type,
    replyToUserId: this.replyToUserId,
    replyToDisplayName: this.displayName,
    replyType: 1,
    content: this.formatWord(this.message),
    docJson: "",
    fromPlat: 1
  };
  // POST /design/bbs/addInteractReply
}
```

---

### 17. 成绩(grade) - 7个API

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 学生成绩 | GET | `/grade/getStuGrade` | 获取学生成绩 |
| 成绩列表 | GET | `/grade/getGradeList` | 成绩列表 |
| 额外成绩别名 | GET | `/grade/gradeExtra/getGradeExtraAlias` | 额外成绩别名 |
| 额外权重 | GET | `/grade/weight/getExtraWeight` | 额外权重 |
| 课堂评分 | GET | `/grade/weight/getFaceRating` | 课堂评分权重 |
| 权重 | GET | `/grade/weight/getWeight` | 获取权重 |
| 按课程权重 | GET | `/grade/weight/getWeightByOpenCourse` | 课程权重 |

---

### 18. 资源(resource) - 10个API

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 预览(Office) | GET | `/resource/preview/getOssOfficeByUrl` | Office文档预览 |
| 预览(材料) | GET | `/resource/preview/getMeterialPreviewByUrl` | 材料预览 |
| 缩略图 | GET | `/resource/preview/getPreviewThumbnail` | 缩略图预览 |
| **下载** | **POST** | **`/resource/down/getDownUrlByUrl`** | **获取下载链接** |
| 我的资源 | GET | `/resource/myResource/getList` | 资源列表 |
| 文档分类 | GET | `/resource/docCategory/getDocCategory` | 文档分类 |
| 学校文档 | GET | `/resource/schoolDoc/schoolCheckDoc` | 学校文档审核 |
| 手写板 | GET | `/resource/tpDocHandwriting/queryByObjectId` | 手写板数据 |

**下载链接获取**:
```
POST /resource/down/getDownUrlByUrl
Content-Type: application/x-www-form-urlencoded
Body: url=资源URL&fileName=文件名
```

---

### 19. 其他模块

#### 课堂纪律(classRequire) - 5个API
| API | 方法 | 路径 |
|-----|------|------|
| 编辑纪律要求 | POST | `/faceteach/classRequire/editRequire` |
| 获取纪律信息 | GET | `/faceteach/classRequire/getClassRequireInfo` |
| 获取纪律学生列表 | GET | `/faceteach/classrequirestu/getStuRequireList` |
| 获取纪律回复列表 | GET | `/faceteach/classrequirereply/getAllReplyList` |
| 保存纪律回复 | POST | `/faceteach/classrequirereply/saveReply` |
| 更新纪律评分 | POST | `/faceteach/classrequirereply/updateGrade` (setScore) |

#### 测验(test) - 5个API
| API | 方法 | 路径 |
|-----|------|------|
| 编辑测验 | GET | `/faceteach/test/edit` |
| 查看测验 | GET | `/faceteach/test/view` |
| 答题统计 | GET | `/faceteach/test/answerStat` |
| 对错统计 | GET | `/faceteach/test/rightOrWrongStat` |
| 更新测验 | POST | `/faceteach/test/update` |

#### 直播(liveClass) - 6个API
| API | 方法 | 路径 |
|-----|------|------|
| 直播列表 | GET | `/faceteach/live/class/list` |
| 直播详情 | GET | `/faceteach/live/class/get` |
| 按ID获取 | GET | `/faceteach/live/class/getLiveClassById` |
| 学生列表 | GET | `/faceteach/live/class/stu/list` |
| 保存直播 | POST | `/faceteach/live/class/saveLiveClass` (urlencoded) |
| 删除直播 | POST | `/faceteach/live/class/delete` (urlencoded) |

#### 教学过程(teachingProcess) - 2个API
| API | 方法 | 路径 |
|-----|------|------|
| 学生教学过程 | GET | `/faceteach/teachingProcess/getStuTeachingProcess` |
| 教师教学过程 | GET | `/faceteach/teachingProcess/getTeachingProcess` |

#### 基础(base) - 6个API
| API | 方法 | 路径 |
|-----|------|------|
| 省份列表 | GET | `/base/address/getPrivice` |
| 城市列表 | GET | `/base/address/getCity` |
| 学校列表 | GET | `/base/school/getSchoolListByFaceteach` |
| 学校名称 | GET | `/base/school/getSchoolName` |
| 未读消息 | GET | `/base/tpBaseInternalEmail/unread` |
| 更新备注 | POST | `/base/tpBaseInternalEmail/updateRemark` (urlencoded) |

#### 统计(coursestatistic) - 2个API
| API | 方法 | 路径 |
|-----|------|------|
| 课程统计 | GET | `/coursestatistic/home/getStatisticCourseCensus` |
| 更新时间 | GET | `/coursestatistic/home/saveStatisticUpdateTime` |

#### 弹幕(barrage) - 2个API
| API | 方法 | 路径 |
|-----|------|------|
| 获取弹幕 | GET | `/faceteach/Barrage/getStuBarrageById` |
| 发送弹幕 | POST | `/screen/barrage/saveBarrage` |

#### 面对面课程(faceteach) - 6个API
| API | 方法 | 路径 |
|-----|------|------|
| 获取详情 | GET | `/faceteach/get` |
| 分页列表 | GET | `/faceteach/getByPage` |
| 课堂详情 | GET | `/faceteach/getFaceClassById` |
| 编辑课堂 | POST | `/faceteach/edit` |
| 删除课堂 | POST | `/faceteach/delete` (deleteTeach) |
| 课程计数 | GET | `/faceteach/scheduleCount` |
| 学生排课 | GET | `/faceteach/stu/scheduleByAll` |
| 学生分页 | GET | `/faceteach/stu/getByPage` |

#### 实习(internship) - 2个API
| API | 方法 | 路径 |
|-----|------|------|
| 保存公司信息 | POST | `/subject/internshipAdmin/saveCompanyInfo` (urlencoded) |
| 保存岗位信息 | POST | `/subject/internshipAdmin/savePostInfo` (urlencoded) |

---

## 四、安全漏洞汇总

### 🚨 高危漏洞

| 漏洞 | API | 风险等级 | 描述 |
|------|-----|----------|------|
| **签到答案泄露** | `GET /faceteach/sign/get` | 🔴 高危 | 返回签到验证码signCode、GPS坐标经纬度，学生可绕过签到验证 |
| **问卷统计泄露** | `GET /faceteach/questionnaire/getQuestionAnswerInfo` | 🟡 中危 | 返回各选项选择人数，可推测正确答案 |

### ⚠️ 潜在风险

| 风险 | API | 描述 |
|------|-----|------|
| 学习进度伪造 | `GET /design/study/saveStudyCellInfo` | 使用GET方法修改数据，可伪造studyTime刷课 |
| 无频率限制 | 上述大部分POST接口 | 未发现请求频率限制，可批量自动操作 |
| Token无绑定 | Header token | Token仅通过Header传递，可能被盗用 |
| 课堂码暴力破解 | 课堂码仅6位 | 6位数字课堂码可暴力枚举加入课堂 |

---

## 五、自动化可行性矩阵

| 模块 | 自动化目标 | 可行性 | 关键参数 | 难度 |
|------|-----------|--------|----------|------|
| 签到 | 自动签到 | ✅ 完全可行 | faceTeachId + sign/get泄露的验证码/坐标 | ⭐ 简单 |
| 讨论 | 自动回复 | ✅ 完全可行 | discussId + content | ⭐ 简单 |
| 头脑风暴 | 自动提交观点 | ✅ 完全可行 | brainstormId + answer + faceTeachId | ⭐ 简单 |
| 投票 | 自动投票 | ✅ 完全可行 | voteId + content(选项sortOrder) | ⭐ 简单 |
| 问卷 | 自动填写 | ✅ 可行 | questionnaireId + faceTeachId + 答案 | ⭐⭐ 中等 |
| 课件/刷课 | 自动标记完成 | ✅ 完全可行 | cellId + tokenId + studyTime=30循环 | ⭐⭐ 中等 |
| 作业/考试 | 自动答题 | ⚠️ 可行但复杂 | workexamId + stuAnswerJson | ⭐⭐⭐ 复杂 |
| 评价 | 自动评价 | ✅ 可行 | faceTeachId + 评价数据 | ⭐⭐ 中等 |
| 课堂码 | 自动加入 | ✅ 完全可行 | classroomCode(6位) / inviteCode | ⭐ 简单 |
| PK小组 | 自动加入 | ✅ 可行 | faceTeachId + groupPkId + randomCode | ⭐⭐ 中等 |

---

## 六、API总数统计

| 模块 | API数量 |
|------|---------|
| course(课程) | 57 |
| workexam(作业考试) | 41 |
| pk/group(PK小组) | 35 |
| bbs(讨论互动) | 23 |
| cell/courseware(课件) | 20 |
| activity(活动) | 10 |
| resource(资源) | 10 |
| sign(签到) | 9 |
| base(基础) | 6 |
| questionnaire(问卷) | 12 |
| live(直播) | 6 |
| quiz(测验) | 8 |
| grade(成绩) | 7 |
| user(用户) | 8 |
| discuss(课堂讨论) | 8 |
| brainstorm(头脑风暴) | 5 |
| evaluation(评价) | 4 |
| 其他(faceteach等) | ~40 |
| **总计** | **~312** |

---

## 七、重要枚举值

### 活动类型(type)
从activity/stu/list返回:
- `1` = 签到
- `2` = 投票
- `3` = 问卷
- `4` = 讨论
- `5` = 头脑风暴
- `6` = 测验/抢答
- `7` = PK
- `8` = 评价
- `9` = 课堂纪律

### 活动状态(state)
- `1` = 未开始
- `2` = 进行中
- `3` = 已结束

### 签到类型(signType)
- `0` = 签到
- `1` = 签退

### 投票类型(voteType)
- `1` = 正确错误
- `2` = 赞成反对
- `3` = 单选
- `4` = 多选

### 问卷题目类型(questionType)
- `1` = 单选
- `2` = 多选
- `3` = 正确错误
- `4` = 赞成反对
- `5` = 问答题

### 数据源(dataSource)
- `2` = Android APP
- `3` = iOS APP
- `4` = H5/Web

### 登录参数
- `clientId`: `4`
- `sourceType`: `4`
- `terminalType`: `h5`

### 课程加入方式(joinWays)
- `1` = 邀请码或扫码加入
- `2` = 禁止加入

### 课件资源类型(category)
- `video` = 视频
- `mp3` = 音频
- `pdf`/`doc`/`ppt` 等 = 文档

### 学习进度(cellProcess)
- `0` = 未开始
- `1-99` = 学习中
- `100` = 已完成

---

*文档生成时间: 2026-04-24*
*逆向来源: chunk-85f99c46.564a8d01.js*

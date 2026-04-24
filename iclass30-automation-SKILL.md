---
name: iclass30-automation
description: 自动化操作iclass30在线教育平台（C30在线），包括登录、查看课程活动、自动签到/签退。账号2504140523，高旗瑞同学。已部署systemd守护进程。
---

# iclass30 平台自动化

## 基本信息
- URL: `https://px.iclass30.com/onlineC30/#/login`
- 账号: 2504140523
- 密码: 114114Aa@
- 用户: 高旗瑞同学（秀山校区）

## 自动签到/签退（已部署）

**脚本**: `/root/.hermes/scripts/iclass30_autosign.py`
**服务**: `c30-autosign.service`（已 enabled，开机自启）

### 用法
```bash
python3 iclass30_autosign.py              # 单次执行
python3 iclass30_autosign.py --dry-run     # 仅查看状态
python3 iclass30_autosign.py --sign-in     # 只处理签到
python3 iclass30_autosign.py --sign-out    # 只处理签退
python3 iclass30_autosign.py --daemon      # 守护进程模式
```

### 服务管理
```bash
systemctl status c30-autosign              # 查看状态
systemctl restart c30-autosign             # 重启
journalctl -u c30-autosign -f              # 查看实时日志
```

### 轮询策略（课表驱动 v3）
- 每天凌晨拉课表缓存本地（6小时有效），精确知道何时有课
- 课前5分钟 → 每1分钟（快速捕获）
- 课中 → 每2分钟（常规监控）
- 课间/无课 → 每30分钟（备用）
- 周末 → 每2小时
- 请求量从368次/天降到66次/天（减少82%）
- C30平台**没有签到的实时推送机制**，socket.io仅用于视频通话，轮询是唯一方案

### 自动化逻辑（v3 课表驱动）
1. 登录获取token
2. 每天拉取课表缓存本地
3. 根据课表调度轮询频率（课前1min/课中2min/课间30min/周末2h）
4. 获取今日课堂 → 遍历活动列表
5. 对 activityType=1(签到) 或 9(签退) 的活动：
   - 查询签到状态 → 已签跳过
   - activityPattern=1(普通) → 直接调participate
   - activityPattern=2/3(扫码/手势) → 先调sign/get获取答案，再传给participate
   - 活动已结束未签到 → alert通知介入
   - 未知模式 → alert通知介入
6. 守护进程模式：循环执行，已处理ID去重
7. 异常写alert文件，hermes cron每5分钟检查（当前已暂停通知）

## HTTP API 参考

**网关**: `https://pxservice.iclass30.com/gatewayApi/`
**认证**: 请求 Header 加 `token: {token}`

### 1. 登录
`GET /user/portal/newLoginApp?userName=&password=&clientId=4&sourceType=4&terminalType=h5&userId=`
返回 result 中含 token（⚠️ result 是 dict，需 `result["token"]` 取值，不是纯字符串）

### 2. 今日课堂
`GET /faceteach/stu/getListByAll?startDate=2026-04-24&endDate=2026-04-24&page=1&pageSize=50`
每个课堂含: id(faceTeachId), courseId, openCourseId, courseName, state(2=进行中,3=已结束)

### 3. 活动列表
`GET /faceteach/activity/stu/list?classState=2&faceTeachId={faceTeachId}`
每个活动含: id(signId), activityType(1=签到,9=签退), activityPattern(1=普通,2=扫码,3=手势), state(2=进行中,3=已结束), title, faceTeachId

### 4. 签到状态
`GET /faceteach/sign/study/getStudyData?signId={signId}`
返回 result.studySignState: 0=未签到, 1=已签到; code=-200 也表示未签到

### 5. 执行签到/签退（⚠️ 关键！）
`POST /faceteach/sign/study/participate`
**必须用 form-urlencoded**（`requests.post(url, data=body)`），不能用 JSON（`json=body`），否则返回502！
Body: `{"signPatternData": "", "signId": "活动id", "centerPoint": "{}"}`
- `code=200` → 签到成功
- `code=-200` → "请勿重复签到或签退！"（已签过的活动）

⚠️ **之前的错误路径 `stuSignIn` 是404，正确路径是 `participate`**（从chunk JS逆向 `Object(r["F"])` 映射确认）

## 浏览器自动化注意事项

**仅当HTTP API不够用时才用浏览器方式。**

- browser_click 对SPA元素经常失效，用console点击或Vue Router导航
- 页面快照经常 element_count:0，用vision截屏或console确认
- Token存cookie，页面刷新会丢失session，需重新登录
- 进入课堂用 `router.push({name:'actListTabbar', params:{activityId, state, courseId, openCourseId}})`

### console点击方法
```javascript
const items = document.querySelectorAll('*');
for (const item of items) {
    if (item.textContent.trim() === '目标文字' && item.offsetParent !== null && item.children.length === 0) {
        item.click(); break;
    }
}
```

### 首页数据获取
- 课堂列表: 遍历Vue组件找 `$data.classList`
- 活动列表: 遍历Vue组件找 `$data.actlist`

## ⚠️ 关键陷阱（实测踩坑）

| 路径 | 用途 |
|------|------|
| `/login` | 登录页 |
| `/home` | 学生首页 |
| `/actListTabbar/:activityId/:state/:courseId?/:openCourseId?` | 课堂活动列表 |
| `/signIn/:activityId/:typeId` | 签到/签退页 |
| `/discusslist/:activityId/:typeId` | 讨论 |
| `/brainStormlist/:activityId/:typeId` | 头脑风暴 |
| `/stuCourse` | 课程中心 |

### 关键漏洞：sign/get 直接返回签到答案！
**`GET /faceteach/sign/get?signId={signId}`** 返回：
- `signPatternType=1` → 普通签到，signPatternData为空
- `signPatternType=2` → 扫码/手势签到，signPatternData含答案（如 `[0,1,3,4]`）
- `refreshQr` → 是否动态刷新二维码
- `range` → 位置范围(米)，`centerPoint` → 位置中心

**这意味着所有签到类型都可以自动完成！**
1. 普通签到(pattern=1): 直接调participate，signPatternData=""
2. 手势签到(pattern=2/3): 先调sign/get获取signPatternData，再传入participate
3. 扫码签到(pattern=2): 同手势签到，答案就在signPatternData里

**验证结果：**
- participate: 已签到返回 code:-200 "请勿重复签到"
- sign/get: 返回完整配置含答案
- signPatternData格式兼容: 空字符串、`[0,1,3,4]`、`0134` 三种格式都通过服务端参数校验

### JS逆向方法论
1. Vue组件中 `Object(r["F"])` 形式引用的API，r来自 `i("模块ID")` 导入
2. 懒加载路由组件在chunk文件中，路由注册处可找到chunk名（如signIn → chunk-85f99c46 → 模块927c）
3. API变量定义块在chunk JS中，格式: `变量名=function(t){return s["a/b"]("/gatewayApi/xxx",t,"","actionType")}`
4. `s["a"]` = GET, `s["b"]` = POST
5. contentType参数控制格式: ""=JSON, "urlencoded"=form, "participate"/"involve"/"setScore"等=标记操作类型
6. 完整逆向文档: https://buyi.nyc.mn/d/USZzhI9pB5

## 实时推送与轮询优化

**C30没有签到实时推送。** socket.io仅用于视频通话。只能轮询。

**课表驱动优化（减少82%请求）：**
- 凌晨拉课表 → 精确预知有课时段
- 课前5分钟 → 每1分钟轮询
- 课中 → 每2分钟
- 课间/无课 → 每30分钟
- 周末 → 每2小时
- 检测到签到后立即执行并暂停该课堂

## 完整签到API（JS逆向）

| API | 方法 | 用途 |
|-----|------|------|
| `/faceteach/sign/get?signId=` | GET | 获取详情（含答案！） |
| `/faceteach/sign/study/getStudyData?signId=` | GET | 查状态(0=未签,1=已签) |
| `/faceteach/sign/study/participate` | POST(form) | 执行签到（核心） |
| `/faceteach/sign/study/list?signId=` | GET | 签到列表 |
| `/faceteach/sign/stats/get?signId=` | GET | 统计 |

**JS逆向要点：**
- signIn组件在chunk模块927c，`Object(r["A"])`=getStudyData, `Object(r["F"])`=participate
- 变量映射: l=getStudyData, u=participate
## 其他模块自动化API（已完整逆向312个API）

完整逆向文档: https://buyi.nyc.mn/d/USZzhI9pB5

### 讨论(discuss) - 自动提交回复
`POST /faceteach/discuss/reply/add` body: {discussId, content, sourceType:1, parentId:"0", file:"[]"}

### 头脑风暴(brainstorm) - 自动提交观点
`POST /faceteach/brainstormstu/addBrainStormStu` body: {brainstormId, answer, faceTeachId, file:"[]"}

### 投票(vote) - 自动投票
`POST /faceteach/vote/study/participate` data: {voteId, content:"1,3"} (选项sortOrder逗号分隔)
先 `GET /faceteach/vote/get?voteId=xxx` 获取选项

### 问卷(questionnaire) - 自动填写
`POST /faceteach/questionnaire/saveQuestionStuQues` data: {questionnaireId, faceTeachId, answerJson}
⚠️ `GET /questionnaire/getQuestionAnswerInfo` 返回选项统计，可推测正确答案

### 课件/刷课(cell/study) - 自动标记完成
`GET /design/study/saveStudyCellInfo?cellId=xxx&tokenId=xxx&studyTime=30` 每30秒调用一次
⚠️ 用GET请求修改数据，可伪造学习进度

### 课堂码加入(involve)
`POST /faceteach/activity/stu/involve` data: {classroomCode:"6位码"} contentType:"involve"

### 活动类型枚举
1=签到, 2=投票, 3=问卷, 4=讨论, 5=头脑风暴, 6=测验/抢答, 7=PK, 8=评价, 9=签退

## ⚠️ 关键陷阱（实测踩坑）
1. **签到API是 `participate` 不是 `stuSignIn`**。JS源码中 `Object(r["F"])` 映射到 `participate`，需要逆向chunk JS才能确认真实路径
2. **参数必须 form-urlencoded**，`requests.post(url, data=body)`，不能用 `json=body`（返回502）
3. **登录返回值是dict**，需要 `result["token"]` 取token，不是直接用 result 字符串
4. **"推送到 buyi.nyc.mn" = 用 tgState API 上传文件**，不要改 Caddy/DNS/服务器配置
5. **C30没有签到实时推送**，socket.io只用于视频通话，只能轮询

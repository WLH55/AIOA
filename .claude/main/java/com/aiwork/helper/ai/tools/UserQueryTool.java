/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.ai.tools;

import com.aiwork.helper.service.UserService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.tool.annotation.Tool;
import org.springframework.ai.tool.annotation.ToolParam;
import org.springframework.stereotype.Component;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 用户查询工具
 * 提供用户名到用户ID的转换功能
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class UserQueryTool {

    private final UserService userService;

    @Tool(description = "根据用户名查询用户ID。当需要将用户名（如'张三'）转换为系统用户ID时使用。返回用户ID字符串，如果找不到返回null。")
    public String getUserIdByName(
            @ToolParam(description = "用户名，如'张三'") String userName
    ) {
        log.info("Tool调用 - getUserIdByName: userName={}", userName);

        if (userName == null || userName.trim().isEmpty()) {
            log.warn("用户名为空");
            return null;
        }

        try {
            String userId = userService.getUserIdByName(userName.trim());
            if (userId != null) {
                log.info("找到用户: {} -> {}", userName, userId);
                return userId;
            } else {
                log.warn("未找到用户: {}", userName);
                return null;
            }
        } catch (Exception e) {
            log.error("查询用户ID失败: userName={}", userName, e);
            return null;
        }
    }
}

/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.dto.request;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 完成待办请求
 * 对应Go版本: internal/domain/domain.go FinishedTodoReq
 */
@Data
public class FinishTodoRequest {

    /**
     * 用户ID
     */
    @NotBlank(message = "用户ID不能为空")
    private String userId;

    /**
     * 待办ID
     */
    @NotBlank(message = "待办ID不能为空")
    private String todoId;
}

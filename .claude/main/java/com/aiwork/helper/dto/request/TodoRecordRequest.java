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
 * 待办操作记录请求
 * 对应Go版本: internal/domain/domain.go TodoRecord
 */
@Data
public class TodoRecordRequest {

    /**
     * 待办ID
     */
    @NotBlank(message = "待办ID不能为空")
    private String todoId;

    /**
     * 记录内容
     */
    @NotBlank(message = "记录内容不能为空")
    private String content;

    /**
     * 图片URL
     */
    private String image;
}

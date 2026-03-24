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
 * 修改密码请求
 * 对应Go版本: internal/domain/domain.go UpdatePasswordReq
 */
@Data
public class UpdatePasswordRequest {

    /**
     * 用户ID
     */
    @NotBlank(message = "用户ID不能为空")
    private String id;

    /**
     * 原密码
     */
    @NotBlank(message = "原密码不能为空")
    private String oldPwd;

    /**
     * 新密码
     */
    @NotBlank(message = "新密码不能为空")
    private String newPwd;
}
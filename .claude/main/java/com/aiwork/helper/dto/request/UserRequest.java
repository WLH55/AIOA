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
 * 用户请求
 * 对应Go版本: internal/domain/domain.go User
 */
@Data
public class UserRequest {

    /**
     * 用户ID (编辑时需要)
     */
    private String id;

    /**
     * 用户名
     */
    @NotBlank(message = "用户名不能为空")
    private String name;

    /**
     * 密码
     */
    private String password;

    /**
     * 状态 (0-禁用, 1-启用)
     */
    private Integer status;
}

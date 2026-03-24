/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.dto.request;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 删除部门用户请求
 * 对应Go版本: internal/domain/domain.go RemoveDepartmentUser
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RemoveDepartmentUserRequest {

    /**
     * 部门ID
     */
    @NotBlank(message = "部门ID不能为空")
    private String depId;

    /**
     * 用户ID
     */
    @NotBlank(message = "用户ID不能为空")
    private String userId;
}

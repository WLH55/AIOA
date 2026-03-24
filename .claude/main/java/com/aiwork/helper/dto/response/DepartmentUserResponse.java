/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 部门用户响应
 * 对应Go版本: internal/domain/domain.go DepartmentUser
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DepartmentUserResponse {

    /**
     * 关联ID
     */
    private String id;

    /**
     * 用户ID
     * JSON字段名: user (匹配Go版本)
     */
    @JsonProperty("user")
    private String userId;

    /**
     * 部门ID
     * JSON字段名: dep (匹配Go版本)
     */
    @JsonProperty("dep")
    private String depId;

    /**
     * 用户姓名
     */
    private String userName;
}
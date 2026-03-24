/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.dto.request;

import lombok.Data;

import java.util.List;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 用户列表查询请求
 * 对应Go版本: internal/domain/domain.go UserListReq
 */
@Data
public class UserListRequest {

    /**
     * 用户ID列表
     */
    private List<String> ids;

    /**
     * 用户名模糊搜索
     */
    private String name;

    /**
     * 页码 (从1开始)
     */
    private Integer page = 1;

    /**
     * 每页数量
     */
    private Integer count = 10;
}
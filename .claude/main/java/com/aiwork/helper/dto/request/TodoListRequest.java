/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.dto.request;

import lombok.Data;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 待办列表查询请求
 * 对应Go版本: internal/domain/domain.go TodoListReq
 */
@Data
public class TodoListRequest {

    /**
     * 待办ID
     */
    private String id;

    /**
     * 执行人用户ID (查询该用户作为执行人的待办)
     */
    private String userId;

    /**
     * 页码 (从1开始)
     */
    private Integer page = 1;

    /**
     * 每页数量
     */
    private Integer count = 10;

    /**
     * 开始时间 (Unix时间戳-秒)
     */
    private Long startTime;

    /**
     * 结束时间 (Unix时间戳-秒)
     */
    private Long endTime;
}

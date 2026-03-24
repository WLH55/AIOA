/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 待办列表响应
 * 对应Go版本: internal/domain/domain.go TodoListResp
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TodoListResponse {

    /**
     * 总记录数
     */
    private Long count;

    /**
     * 待办列表
     */
    private List<TodoResponse> data;
}

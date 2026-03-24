/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.dto.request;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 审批列表请求
 * 对应Go版本: internal/domain/domain.go ApprovalListReq
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ApprovalListRequest {

    /**
     * 用户ID
     */
    private String userId;

    /**
     * 操作类型 (1=我提交的, 2=待我审批的)
     * 对应Go版本: ApprovalOptionType
     */
    private Integer type;

    /**
     * 页码
     */
    private Integer page;

    /**
     * 每页数量
     */
    private Integer count;
}
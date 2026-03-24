/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.service;

import com.aiwork.helper.dto.request.ApprovalListRequest;
import com.aiwork.helper.dto.request.ApprovalRequest;
import com.aiwork.helper.dto.request.DisposeRequest;
import com.aiwork.helper.dto.response.ApprovalListResponse;
import com.aiwork.helper.dto.response.ApprovalResponse;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 审批服务接口
 * 对应Go版本: internal/logic/approval.go Approval接口
 */
public interface ApprovalService {

    /**
     * 获取审批详情
     * 对应Go: Info(ctx, req)
     */
    ApprovalResponse info(String id);

    /**
     * 创建审批申请
     * 对应Go: Create(ctx, req)
     */
    String create(ApprovalRequest request);

    /**
     * 处理审批（通过/拒绝/撤销）
     * 对应Go: Dispose(ctx, req)
     */
    void dispose(DisposeRequest request);

    /**
     * 获取审批列表
     * 对应Go: List(ctx, req)
     */
    ApprovalListResponse list(ApprovalListRequest request);
}

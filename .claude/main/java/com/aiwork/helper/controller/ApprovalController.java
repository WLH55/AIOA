/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.controller;

import com.aiwork.helper.common.Result;
import com.aiwork.helper.dto.request.ApprovalListRequest;
import com.aiwork.helper.dto.request.ApprovalRequest;
import com.aiwork.helper.dto.request.DisposeRequest;
import com.aiwork.helper.dto.response.ApprovalListResponse;
import com.aiwork.helper.dto.response.ApprovalResponse;
import com.aiwork.helper.service.ApprovalService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 审批控制器
 * 对应Go版本: internal/handler/api/approval.go
 */
@RestController
@RequestMapping("/v1/approval")
@RequiredArgsConstructor
public class ApprovalController {

    private final ApprovalService approvalService;

    /**
     * 获取审批详情
     * 对应Go: GET /v1/approval/:id
     */
    @GetMapping("/{id}")
    public Result<ApprovalResponse> info(@PathVariable String id) {
        ApprovalResponse response = approvalService.info(id);
        return Result.ok(response);
    }

    /**
     * 创建审批申请
     * 对应Go: POST /v1/approval
     */
    @PostMapping
    public Result<String> create(@Valid @RequestBody ApprovalRequest request) {
        String id = approvalService.create(request);
        return Result.ok(id);
    }

    /**
     * 处理审批（通过/拒绝/撤销）
     * 对应Go: PUT /v1/approval/dispose
     */
    @PutMapping("/dispose")
    public Result<Void> dispose(@Valid @RequestBody DisposeRequest request) {
        approvalService.dispose(request);
        return Result.ok();
    }

    /**
     * 获取审批列表
     * 对应Go: GET /v1/approval/list
     */
    @GetMapping("/list")
    public Result<ApprovalListResponse> list(@Valid ApprovalListRequest request) {
        ApprovalListResponse response = approvalService.list(request);
        return Result.ok(response);
    }
}
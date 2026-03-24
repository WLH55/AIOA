/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.service;

import com.aiwork.helper.dto.request.FinishTodoRequest;
import com.aiwork.helper.dto.request.TodoListRequest;
import com.aiwork.helper.dto.request.TodoRecordRequest;
import com.aiwork.helper.dto.request.TodoRequest;
import com.aiwork.helper.dto.response.TodoInfoResponse;
import com.aiwork.helper.dto.response.TodoListResponse;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 待办事项服务接口
 * 对应Go版本: internal/logic/todo.go Todo接口
 */
public interface TodoService {

    /**
     * ���取待办详情
     * 对应Go: Info(ctx, req)
     */
    TodoInfoResponse info(String id);

    /**
     * 创建待办
     * 对应Go: Create(ctx, req)
     */
    String create(TodoRequest request);

    /**
     * 编辑待办
     * 对应Go: Edit(ctx, req)
     */
    void edit(TodoRequest request);

    /**
     * 删除待办
     * 对应Go: Delete(ctx, req)
     */
    void delete(String id);

    /**
     * 完成待办
     * 对应Go: Finish(ctx, req)
     */
    void finish(FinishTodoRequest request);

    /**
     * 创建待办操作记录
     * 对应Go: CreateRecord(ctx, req)
     */
    void createRecord(TodoRecordRequest request);

    /**
     * 待办列表
     * 对应Go: List(ctx, req)
     */
    TodoListResponse list(TodoListRequest request);
}

/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.service;

import com.aiwork.helper.dto.request.*;
import com.aiwork.helper.dto.response.DepartmentResponse;
import com.aiwork.helper.dto.response.DepartmentTreeResponse;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 部门服务接口
 * 对应Go版本: internal/logic/department.go Department接口
 */
public interface DepartmentService {

    /**
     * 获取部门树结构（SOA）
     * 对应Go: Soa(ctx)
     */
    DepartmentTreeResponse soa();

    /**
     * 获取部门详情
     * 对应Go: Info(ctx, req)
     */
    DepartmentResponse info(String id);

    /**
     * 创建部门
     * 对应Go: Create(ctx, req)
     */
    void create(DepartmentRequest request);

    /**
     * 更新部门
     * 对应Go: Edit(ctx, req)
     */
    void edit(DepartmentRequest request);

    /**
     * 删除部门
     * 对应Go: Delete(ctx, req)
     */
    void delete(String id);

    /**
     * 设置部门用户
     * 对应Go: SetDepartmentUsers(ctx, req)
     */
    void setDepartmentUsers(SetDepartmentUsersRequest request);

    /**
     * 添加部门用户（级联到上级部门）
     * 对应Go: AddDepartmentUser(ctx, req)
     */
    void addDepartmentUser(AddDepartmentUserRequest request);

    /**
     * 删除部门用户（级联从上级部门删除）
     * 对应Go: RemoveDepartmentUser(ctx, req)
     */
    void removeDepartmentUser(RemoveDepartmentUserRequest request);

    /**
     * 获取用户部门信息（包含完整的上级部门层级）
     * 对应Go: DepartmentUserInfo(ctx, req)
     */
    DepartmentResponse departmentUserInfo(String userId);
}

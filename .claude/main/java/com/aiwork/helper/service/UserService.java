/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.service;

import com.aiwork.helper.dto.request.LoginRequest;
import com.aiwork.helper.dto.request.UpdatePasswordRequest;
import com.aiwork.helper.dto.request.UserListRequest;
import com.aiwork.helper.dto.request.UserRequest;
import com.aiwork.helper.dto.response.LoginResponse;
import com.aiwork.helper.dto.response.UserListResponse;
import com.aiwork.helper.dto.response.UserResponse;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 用户服务接口
 * 对应Go版本: internal/logic/user.go User接口
 */
public interface UserService {

    /**
     * 用户登录
     * 对应Go: Login(ctx, req)
     */
    LoginResponse login(LoginRequest request);

    /**
     * 获取用户信息
     * 对应Go: Info(ctx, req)
     */
    UserResponse info(String id);

    /**
     * 创建用户
     * 对应Go: Create(ctx, req)
     */
    void create(UserRequest request);

    /**
     * 编辑用户
     * 对应Go: Edit(ctx, req)
     */
    void edit(UserRequest request);

    /**
     * 删除用户
     * 对应Go: Delete(ctx, req)
     */
    void delete(String id);

    /**
     * 用户列表
     * 对应Go: List(ctx, req)
     */
    UserListResponse list(UserListRequest request);

    /**
     * 修改密码
     * 对应Go: UpdatePassword(ctx, req)
     */
    void updatePassword(UpdatePasswordRequest request);

    /**
     * 初始化系统管理员用户
     * 对应Go: svc/servicecontext.go initUser
     */
    void initAdminUser();

    /**
     * 根据用户名获取用户ID
     * 对应Go版本: user_list工具的功能
     * @param name 用户名
     * @return 用户ID，如果找不到返回null
     */
    String getUserIdByName(String name);
}

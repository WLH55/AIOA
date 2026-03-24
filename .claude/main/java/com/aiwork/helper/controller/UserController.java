/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.controller;

import com.aiwork.helper.common.Result;
import com.aiwork.helper.dto.request.LoginRequest;
import com.aiwork.helper.dto.request.UpdatePasswordRequest;
import com.aiwork.helper.dto.request.UserListRequest;
import com.aiwork.helper.dto.request.UserRequest;
import com.aiwork.helper.dto.response.LoginResponse;
import com.aiwork.helper.dto.response.UserListResponse;
import com.aiwork.helper.dto.response.UserResponse;
import com.aiwork.helper.service.UserService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 用户控制器
 * 对应Go版本: internal/handler/api/user.go
 */
@RestController
@RequestMapping("/v1/user")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    /**
     * 用户登录
     * 对应Go: func (h *User) Login(ctx *gin.Context)
     *
     * POST /v1/user/login
     */
    @PostMapping("/login")
    public Result<LoginResponse> login(@Valid @RequestBody LoginRequest request) {
        LoginResponse response = userService.login(request);
        return Result.ok(response);
    }

    /**
     * 获取用户信息
     * 对应Go: func (h *User) Info(ctx *gin.Context)
     *
     * GET /v1/user/{id}
     */
    @GetMapping("/{id}")
    public Result<UserResponse> info(@PathVariable String id) {
        UserResponse response = userService.info(id);
        return Result.ok(response);
    }

    /**
     * 创建用户
     * 对应Go: func (h *User) Create(ctx *gin.Context)
     *
     * POST /v1/user
     */
    @PostMapping
    public Result<Void> create(@Valid @RequestBody UserRequest request) {
        userService.create(request);
        return Result.ok();
    }

    /**
     * 编辑用户
     * 对应Go: func (h *User) Edit(ctx *gin.Context)
     *
     * PUT /v1/user
     */
    @PutMapping
    public Result<Void> edit(@Valid @RequestBody UserRequest request) {
        userService.edit(request);
        return Result.ok();
    }

    /**
     * 删除用户
     * 对应Go: func (h *User) Delete(ctx *gin.Context)
     *
     * DELETE /v1/user/{id}
     */
    @DeleteMapping("/{id}")
    public Result<Void> delete(@PathVariable String id) {
        userService.delete(id);
        return Result.ok();
    }

    /**
     * 用户列表
     * 对应Go: func (h *User) List(ctx *gin.Context)
     *
     * GET /v1/user/list
     */
    @GetMapping("/list")
    public Result<UserListResponse> list(UserListRequest request) {
        UserListResponse response = userService.list(request);
        return Result.ok(response);
    }

    /**
     * 修改密码
     * 对应Go: func (h *User) UpdatePassword(ctx *gin.Context)
     *
     * POST /v1/user/password
     */
    @PostMapping("/password")
    public Result<Void> updatePassword(@Valid @RequestBody UpdatePasswordRequest request) {
        userService.updatePassword(request);
        return Result.ok();
    }
}

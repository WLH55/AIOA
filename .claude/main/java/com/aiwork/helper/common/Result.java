/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.common;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Data;

import java.util.HashMap;
import java.util.Map;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 统一响应结果
 * 对应Go版本: pkg/httpx/response.go Response结构体
 */
@Data
@JsonInclude(JsonInclude.Include.NON_NULL)
public class Result<T> {

    /**
     * 响应代码 (200-成功, 500-失败)
     * 对应Go: Response.Code
     */
    private Integer code;

    /**
     * 响应数据
     * 对应Go: Response.Data
     */
    private T data;

    /**
     * 响应消息
     * 对应Go: Response.Msg
     */
    private String msg;

    /**
     * 成功代码
     * 对应Go: SUCCESS = 200
     */
    public static final int SUCCESS = 200;

    /**
     * 失败代码
     * 对应Go: ERROR = 500
     */
    public static final int ERROR = 500;

    /**
     * 成功消息
     * 对应Go: SUCCESSMSG = "success"
     */
    public static final String SUCCESS_MSG = "success";

    /**
     * 失败消息
     * 对应Go: ERRORMSG = "fail"
     */
    public static final String ERROR_MSG = "fail";

    /**
     * 空数据对象
     * 对应Go: NULL = map[string]interface{}{}
     */
    public static final Map<String, Object> NULL = new HashMap<>();

    public Result() {
    }

    public Result(Integer code, T data, String msg) {
        this.code = code;
        this.data = data;
        this.msg = msg;
    }

    /**
     * 成功响应（无数据）
     * 对应Go: Ok(ctx)
     */
    public static <T> Result<T> ok() {
        return new Result<>(SUCCESS, null, SUCCESS_MSG);
    }

    /**
     * 成功响应（带数据）
     * 对应Go: OkWithData(ctx, data)
     */
    public static <T> Result<T> ok(T data) {
        return new Result<>(SUCCESS, data, SUCCESS_MSG);
    }

    /**
     * 成功响应（带数据和消息）
     */
    public static <T> Result<T> ok(T data, String msg) {
        return new Result<>(SUCCESS, data, msg);
    }

    /**
     * 失败响应（默认消息）
     * 对应Go: Fail(ctx)
     */
    public static <T> Result<T> fail() {
        return new Result<>(ERROR, null, ERROR_MSG);
    }

    /**
     * 失败响应（带错误消息）
     * 对应Go: FailWithErr(ctx, err)
     */
    public static <T> Result<T> fail(String msg) {
        return new Result<>(ERROR, null, msg);
    }

    /**
     * 失败响应（带错误代码和消息）
     */
    public static <T> Result<T> fail(Integer code, String msg) {
        return new Result<>(code, null, msg);
    }

    /**
     * 自定义响应
     * 对应Go: Result(ctx, code, data, msg)
     */
    public static <T> Result<T> build(Integer code, T data, String msg) {
        return new Result<>(code, data, msg);
    }
}

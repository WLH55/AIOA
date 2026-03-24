/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.entity.enums;

import lombok.Getter;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 待办事项状态枚举
 */
@Getter
public enum TodoStatus {
    PENDING(1, "待处理"),
    IN_PROGRESS(2, "进行中"),
    FINISHED(3, "已完成"),
    CANCELLED(4, "已取消"),
    TIMEOUT(5, "已超时");

    private final int value;
    private final String description;

    TodoStatus(int value, String description) {
        this.value = value;
        this.description = description;
    }

    public static TodoStatus fromValue(int value) {
        for (TodoStatus status : values()) {
            if (status.value == value) {
                return status;
            }
        }
        return PENDING;
    }
}
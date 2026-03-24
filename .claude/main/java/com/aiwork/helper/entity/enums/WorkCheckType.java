/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.entity.enums;

import lombok.Getter;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 打卡类型枚举
 * 1.上班卡，2.下班卡
 */
@Getter
public enum WorkCheckType {
    ON_WORK(1, "上班卡"),
    OFF_WORK(2, "下班卡");

    private final int value;
    private final String description;

    WorkCheckType(int value, String description) {
        this.value = value;
        this.description = description;
    }

    public static WorkCheckType fromValue(int value) {
        for (WorkCheckType type : values()) {
            if (type.value == value) {
                return type;
            }
        }
        return ON_WORK;
    }
}
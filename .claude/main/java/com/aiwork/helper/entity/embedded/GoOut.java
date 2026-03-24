/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.entity.embedded;

import lombok.Data;
import org.springframework.data.mongodb.core.mapping.Field;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 外出信息 (嵌入文档)
 */
@Data
public class GoOut {

    /**
     * 开始时间
     */
    @Field("startTime")
    private Long startTime;

    /**
     * 结束时间
     */
    @Field("endTime")
    private Long endTime;

    /**
     * 时长 (小时)
     */
    @Field("duration")
    private Float duration;

    /**
     * 外出原因
     */
    @Field("reason")
    private String reason;
}
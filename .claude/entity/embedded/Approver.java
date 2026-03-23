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
 * 审批人 (嵌入文档)
 */
@Data
public class Approver {

    /**
     * 用户ID
     */
    @Field("userId")
    private String userId;

    /**
     * 用户姓名
     */
    @Field("userName")
    private String userName;

    /**
     * 审批状态
     */
    @Field("status")
    private Integer status;

    /**
     * 审批理由
     */
    @Field("reason")
    private String reason;
}

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
 * 待办事项操作记录 (嵌入文档)
 * 用于Todo实体中的records字段
 */
@Data
public class TodoRecord {

    /**
     * 操作用户ID
     */
    @Field("userId")
    private String userId;

    /**
     * 操作用户名
     */
    @Field("userName")
    private String userName;

    /**
     * 操作内容
     */
    @Field("content")
    private String content;

    /**
     * 操作相关图片
     */
    @Field("image")
    private String image;

    /**
     * 操作时间
     */
    @Field("createAt")
    private Long createAt;
}
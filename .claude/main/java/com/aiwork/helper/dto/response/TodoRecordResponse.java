/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 待办操作记录响应
 * 对应Go版本: internal/domain/domain.go TodoRecord
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TodoRecordResponse {

    /**
     * 待办ID
     */
    private String todoId;

    /**
     * 操作用户ID
     */
    private String userId;

    /**
     * 操作用户姓名
     */
    private String userName;

    /**
     * 操作内容
     */
    private String content;

    /**
     * 图片URL
     */
    private String image;

    /**
     * 创建时间
     */
    private Long createAt;
}

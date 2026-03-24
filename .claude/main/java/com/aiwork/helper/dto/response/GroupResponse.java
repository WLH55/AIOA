/**
 * @author: 公众号:IT杨秀才
 * @doc:后端,AI知识进阶,后端面试场景题大全:https://golangstar.cn/
 */
package com.aiwork.helper.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * author:  公众号:IT杨秀才
 * 后端,AI知识进阶,后端面试场景题大全:https://golangstar.cn/
 * 群聊信息响应
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class GroupResponse {

    /**
     * 群ID
     */
    private String groupId;

    /**
     * 群名称
     */
    private String groupName;

    /**
     * 群成员ID列表
     */
    private List<String> memberIds;

    /**
     * 创建者ID
     */
    private String creatorId;

    /**
     * 创建时间
     */
    private Long createAt;
}

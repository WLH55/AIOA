/**
 * @author: 公众号:IT杨秀才
 * @doc:后端,AI知识进阶,后端面试场景题大全:https://golangstar.cn/
 */
package com.aiwork.helper.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * author:  公众号:IT杨秀才
 * 后端,AI知识进阶,后端面试场景题大全:https://golangstar.cn/
 * 添加群成员请求
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AddGroupMembersRequest {

    /**
     * 群ID
     */
    @NotBlank(message = "群ID不能为空")
    private String groupId;

    /**
     * 要添加的成员ID列表
     */
    @NotEmpty(message = "成员列表不能为空")
    private List<String> memberIds;
}

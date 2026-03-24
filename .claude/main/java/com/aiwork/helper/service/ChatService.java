/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.service;

import com.aiwork.helper.dto.websocket.ChatMessage;

import java.util.List;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 聊天服务接口
 * 对应Go版本: internal/logic/chat.go Chat接口
 */
public interface ChatService {

    /**
     * 处理私聊消息
     * 对应Go: PrivateChat(ctx, req)
     */
    void savePrivateChat(ChatMessage message);

    /**
     * 处理群聊消息
     * 对应Go: GroupChat(ctx, req)
     */
    void saveGroupChat(ChatMessage message);

    /**
     * 处理AI聊天请求
     * 对应Go: AIChat(ctx, req)
     * @param userId 用户ID
     * @param content 用户输入内容
     * @param relationId 关联ID（群聊ID等）
     * @param startTime 开始时间（Unix时间戳）
     * @param endTime 结束时间（Unix时间戳）
     * @return AI响应内容
     */
    String handleAIChat(String userId, String content, String relationId, Long startTime, Long endTime);

    /**
     * 获取聊天历史
     * @param conversationId 会话ID
     * @param limit 限制数量
     * @return 聊天消息列表
     */
    List<ChatMessage> getChatHistory(String conversationId, int limit);
}

/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.service.impl;

import com.aiwork.helper.ai.agent.AgentService;
import com.aiwork.helper.dto.websocket.ChatMessage;
import com.aiwork.helper.entity.ChatLog;
import com.aiwork.helper.repository.ChatLogRepository;
import com.aiwork.helper.service.ChatService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 聊天服务实现
 * 使用AgentService处理AI聊天请求（基于Spring AI Function Calling）
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class ChatServiceImpl implements ChatService {

    private final ChatLogRepository chatLogRepository;
    private final AgentService agentService;

    @Override
    public void savePrivateChat(ChatMessage message) {
        log.info("保存私聊消息: from={}, to={}", message.getSendId(), message.getRecvId());
        saveChatLog(message);
    }

    @Override
    public void saveGroupChat(ChatMessage message) {
        log.info("保存群聊消息: from={}, conversationId={}",
                message.getSendId(), message.getConversationId());
        saveChatLog(message);
    }

    @Override
    public String handleAIChat(String userId, String content, String relationId, Long startTime, Long endTime) {
        log.info("处理AI聊天: userId={}, content={}, relationId={}, startTime={}, endTime={}",
                userId, content, relationId, startTime, endTime);

        try {
            // 使用AgentService处理AI聊天 (Spring AI Function Calling)
            // Agent工作流程:
            // 1. 分析用户输入意图
            // 2. 自动选择合适的Tool调用
            // 3. 执行Tool并获取结果
            // 4. 继续推理，可能调用更多Tool
            // 5. 生成最终回复
            String aiResponse = agentService.chat(userId, content, relationId, startTime, endTime);

            log.info("AI响应成功: relationId={}, responseLength={}",
                    relationId, aiResponse != null ? aiResponse.length() : 0);

            return aiResponse;

        } catch (Exception e) {
            log.error("AI聊天处理失败: userId={}, relationId={}",
                    userId, relationId, e);
            return "抱歉，AI服务暂时不可用，请稍后再试。";
        }
    }

    @Override
    public List<ChatMessage> getChatHistory(String conversationId, int limit) {
        log.info("获取聊天历史: conversationId={}, limit={}", conversationId, limit);

        if (conversationId == null || conversationId.isEmpty()) {
            return new ArrayList<>();
        }

        // 查询聊天记录，按发送时间倒序
        PageRequest pageRequest = PageRequest.of(0, limit,
                Sort.by(Sort.Direction.DESC, "sendTime"));

        List<ChatLog> chatLogs = chatLogRepository
                .findByConversationId(conversationId, pageRequest)
                .getContent();

        // 转换为WebSocketMessage
        return chatLogs.stream()
                .map(this::convertToWebSocketMessage)
                .collect(Collectors.toList());
    }

    /**
     * 保存聊天消息到数据库
     */
    private void saveChatLog(ChatMessage message) {
        long currentTime = System.currentTimeMillis() / 1000;

        ChatLog chatLog = new ChatLog();
        chatLog.setConversationId(message.getConversationId());
        chatLog.setSendId(message.getSendId());
        chatLog.setRecvId(message.getRecvId());
        chatLog.setChatType(message.getChatType());
        chatLog.setMsgContent(message.getContent());
        chatLog.setSendTime(currentTime);

        try {
            chatLogRepository.save(chatLog);
            log.debug("聊天消息已保存: id={}", chatLog.getId());
        } catch (Exception e) {
            log.error("保存聊天消息失败", e);
        }
    }

    /**
     * 将ChatLog转换为ChatMessage
     */
    private ChatMessage convertToWebSocketMessage(ChatLog chatLog) {
        return ChatMessage.builder()
                .conversationId(chatLog.getConversationId())
                .sendId(chatLog.getSendId())
                .recvId(chatLog.getRecvId())
                .chatType(chatLog.getChatType())
                .content(chatLog.getMsgContent())
                .contentType(1) // 默认为文字类型
                .build();
    }

    /**
     * 生成会话ID（私聊场景）
     * 根据两个用户ID生成唯一的会话ID
     */
    private String generateConversationId(String userId1, String userId2) {
        // 对用户ID排序，确保相同的两个用户生成相同的会话ID
        List<String> userIds = new ArrayList<>();
        userIds.add(userId1);
        userIds.add(userId2);
        userIds.sort(String::compareTo);

        return String.join("_", userIds);
    }
}

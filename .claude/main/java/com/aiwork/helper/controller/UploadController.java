/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.controller;

import com.aiwork.helper.ai.tools.FileTools;
import com.aiwork.helper.common.Result;
import com.aiwork.helper.dto.response.FileResponse;
import com.aiwork.helper.entity.ChatLog;
import com.aiwork.helper.exception.BusinessException;
import com.aiwork.helper.repository.ChatLogRepository;
import com.aiwork.helper.security.SecurityUtils;
import com.aiwork.helper.service.AIService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.UUID;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 文件上传控制器
 * 对应Go版本: internal/handler/api/upload.go
 */
@Slf4j
@RestController
@RequestMapping("/v1/upload")
@RequiredArgsConstructor
public class UploadController {

    @Value("${upload.savePath:upload/}")
    private String savePath;

    @Value("${server.host:http://localhost:8888}")
    private String host;

    private final ChatLogRepository chatLogRepository;
    private final AIService aiService;

    /**
     * 单文件上传
     * 对应Go: POST /v1/upload/file
     *
     * @param file 上传的文件
     * @param chat 可选参数，如果指定则将文件信息写入聊天记忆
     */
    @PostMapping("/file")
    public Result<FileResponse> uploadFile(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "chat", required = false) String chat) {

        if (file.isEmpty()) {
            throw new BusinessException("上传文件不能为空");
        }

        try {
            // 确保上传目录存在
            Path uploadDir = Paths.get(savePath);
            if (!Files.exists(uploadDir)) {
                Files.createDirectories(uploadDir);
            }

            // 获取原始文件名和扩展名
            String originalFilename = file.getOriginalFilename();
            String extension = "";
            if (originalFilename != null && originalFilename.contains(".")) {
                extension = originalFilename.substring(originalFilename.lastIndexOf("."));
            }

            // 生成唯一文件名（使用UUID代替Go的ksuid）
            String filename = UUID.randomUUID().toString().replace("-", "") + extension;

            // 保存文件
            Path targetPath = uploadDir.resolve(filename);
            Files.copy(file.getInputStream(), targetPath, StandardCopyOption.REPLACE_EXISTING);

            log.info("file upload success: {}", filename);

            // 构建响应
            FileResponse response = FileResponse.builder()
                    .host(host)
                    .file(savePath + filename)
                    .filename(filename)
                    .build();

            // 如果指定了chat参数，将文件信息写入聊天记忆（内存+数据库）
            if (chat != null && !chat.isEmpty()) {
                log.info("file upload with chat context: {}", chat);
                saveFileToMemory(chat, response, originalFilename);
            }

            return Result.ok(response);

        } catch (IOException e) {
            log.error("file upload failed", e);
            throw new BusinessException("文件上传失败: " + e.getMessage());
        }
    }

    /**
     * 多文件上传
     * 对应Go: POST /v1/upload/multiplefiles
     *
     * @param files 上传的文件数组
     */
    @PostMapping("/multiplefiles")
    public Result<Void> uploadMultipleFiles(@RequestParam("files") MultipartFile[] files) {
        // TODO: 实现多文件上传功能
        throw new BusinessException("多文件上传功能暂未实现");
    }

    /**
     * 将文件信息保存到聊天记忆中（内存缓存 + 数据库）
     * 对应Go版本: chat.File() 方法
     * Go 版本使用 userId (ChatId) 作为 memory key，而不是 conversationId
     */
    private void saveFileToMemory(String conversationId, FileResponse fileResp, String originalFilename) {
        try {
            // 获取当前用户ID
            String userId = SecurityUtils.getCurrentUserId();
            if (userId == null) {
                log.warn("无法获取当前用户ID，跳过保存文件到聊天记忆");
                return;
            }

            // 构建文件上传成功的消息
            String message = String.format("文件 \"%s\" 已上传成功，文件路径: %s",
                    originalFilename, fileResp.getFile());

            // 1. 保存到FileTools的内存缓存（关键！供Agent的Tool使用）
            FileTools.saveUploadedFile(userId, fileResp.getFile(), originalFilename);

            // 2. 保存到数据库（持久化）
            ChatLog chatLog = new ChatLog();
            chatLog.setConversationId(conversationId != null ? conversationId : "knowledge");
            chatLog.setSendId(userId);
            chatLog.setRecvId("");
            chatLog.setChatType(1);
            chatLog.setMsgContent(message);
            chatLog.setSendTime(System.currentTimeMillis() / 1000);
            chatLogRepository.save(chatLog);

            // 3. 同时保存到旧的AIService内存（兼容旧逻辑）
            aiService.addMessageToHistory(userId, "user", message);

            log.info("文件信息已保存到聊天记忆: userId={}, file={}", userId, fileResp.getFile());

        } catch (Exception e) {
            log.error("保存文件到聊天记忆失败", e);
            // 不抛出异常，避免影响文件上传功能
        }
    }
}

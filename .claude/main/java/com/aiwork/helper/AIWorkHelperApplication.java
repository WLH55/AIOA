/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.mongodb.repository.config.EnableMongoRepositories;
import org.springframework.scheduling.annotation.EnableAsync;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * AIWorkHelper 主应用类
 * AI智能办公助手系统 - 基于Spring Boot 3.x + Spring AI Alibaba
 *
 * 功能特性:
 * - 用户管理系统
 * - 待办事项管理
 * - 审批流程管理
 * - 部门组织管理
 * - WebSocket实时聊天
 * - AI智能助手 (集成阿里云通义千问)
 * - 知识库检索与更新
 */
@SpringBootApplication
@EnableMongoRepositories
@EnableAsync
public class AIWorkHelperApplication {

    public static void main(String[] args) {
        SpringApplication.run(AIWorkHelperApplication.class, args);
        System.out.println("==============================================");
        System.out.println("AIWorkHelper 启动成功!");
        System.out.println("HTTP API 服务: http://localhost:8888");
        System.out.println("WebSocket 服务: ws://localhost:9000/ws");
        System.out.println("==============================================");
    }
}

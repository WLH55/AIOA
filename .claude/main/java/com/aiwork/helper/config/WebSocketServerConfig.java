/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * WebSocket服务器配置
 * 对应Go版本: Ws.Addr配置
 */
@Data
@Configuration
@ConfigurationProperties(prefix = "websocket.server")
public class WebSocketServerConfig {

    /**
     * WebSocket服务器端口
     */
    private int port = 9000;

    /**
     * WebSocket路径
     */
    private String path = "/ws";
}

/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.config;

import lombok.extern.slf4j.Slf4j;
import org.apache.catalina.connector.Connector;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.embedded.tomcat.TomcatServletWebServerFactory;
import org.springframework.boot.web.server.WebServerFactoryCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 多端口配置
 * 让Spring Boot应用同时监听8888（API）和9000（WebSocket）端口
 * 对应Go版本：API服务在8888端口，WebSocket服务在9000端口
 */
@Slf4j
@Configuration
public class MultiPortConfig {

    @Value("${websocket.server.port:9000}")
    private int websocketPort;

    @Bean
    public WebServerFactoryCustomizer<TomcatServletWebServerFactory> servletContainer() {
        return factory -> {
            factory.addAdditionalTomcatConnectors(createWebSocketConnector());
            log.info("额外的WebSocket连接器配置在端口: {}", websocketPort);
        };
    }

    private Connector createWebSocketConnector() {
        Connector connector = new Connector("org.apache.coyote.http11.Http11NioProtocol");
        connector.setScheme("http");
        connector.setPort(websocketPort);
        return connector;
    }
}
/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.websocket;

import com.aiwork.helper.security.JwtTokenProvider;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.server.ServerHttpRequest;
import org.springframework.http.server.ServerHttpResponse;
import org.springframework.http.server.ServletServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.WebSocketHandler;
import org.springframework.web.socket.server.HandshakeInterceptor;

import java.util.Map;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * WebSocket握手拦截器
 * 负责JWT Token验证和用户身份提取
 * 对应Go版本: internal/handler/ws/ws.go auth()方法
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class WebSocketHandshakeInterceptor implements HandshakeInterceptor {

    private final JwtTokenProvider jwtTokenProvider;

    @Override
    public boolean beforeHandshake(ServerHttpRequest request, ServerHttpResponse response,
                                   WebSocketHandler wsHandler, Map<String, Object> attributes) {
        try {
            String token = null;

            if (request instanceof ServletServerHttpRequest) {
                ServletServerHttpRequest servletRequest = (ServletServerHttpRequest) request;

                // 优先从请求头中获取Token（对应Go的r.Header.Get("websocket")）
                token = servletRequest.getServletRequest().getHeader("websocket");

                // 如果请求头中没有，尝试从URL参数中获取（对应Go的r.URL.Query().Get("token")）
                if (token == null || token.isEmpty()) {
                    token = servletRequest.getServletRequest().getParameter("token");
                }
            }

            // 如果两种方式都没有获取到token，拒绝连接
            if (token == null || token.isEmpty()) {
                log.warn("WebSocket连接被拒绝: 没有提供Token");
                return false;
            }

            // 验证Token并提取用户ID
            if (!jwtTokenProvider.validateToken(token)) {
                log.warn("WebSocket连接被拒绝: Token无效");
                return false;
            }

            String userId = jwtTokenProvider.getUserIdFromToken(token);
            if (userId == null) {
                log.warn("WebSocket连接被拒绝: 无法从Token中提取用户ID");
                return false;
            }

            // 将用户ID和Token存储到WebSocket会话属性中
            // 对应Go的将uid和token传递给handleConn
            attributes.put("userId", userId);
            attributes.put("token", token);

            log.info("WebSocket握手成功: userId={}", userId);
            return true;

        } catch (Exception e) {
            log.error("WebSocket握手失败", e);
            return false;
        }
    }

    @Override
    public void afterHandshake(ServerHttpRequest request, ServerHttpResponse response,
                              WebSocketHandler wsHandler, Exception exception) {
        if (exception != null) {
            log.error("WebSocket握手后处理异常", exception);
        }
    }
}
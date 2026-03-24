/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.ArrayList;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * JWT认证过滤器
 * 拦截所有请求，从Header中提取JWT Token并验证
 * 对应Go版本: internal/middleware/jwt.go
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtTokenProvider jwtTokenProvider;

    /**
     * 过滤器核心逻辑
     * 对应Go: Jwt.Handler
     */
    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {

        try {
            // 从请求中提取JWT Token
            String jwt = getJwtFromRequest(request);

            // 如果Token存在且有效，则设置认证信息
            if (StringUtils.hasText(jwt) && jwtTokenProvider.validateToken(jwt)) {
                // 从Token中获取用户ID
                String userId = jwtTokenProvider.getUserIdFromToken(jwt);

                // 创建认证对象
                // 对应Go: 将userId注入到context中
                UsernamePasswordAuthenticationToken authentication =
                        new UsernamePasswordAuthenticationToken(
                                userId,  // principal - 用户标识
                                null,    // credentials - 凭证(不需要)
                                new ArrayList<>()  // authorities - 权限列表(暂时为空)
                        );

                // 设置请求详情
                authentication.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));

                // 将认证信息设置到Security上下文
                SecurityContextHolder.getContext().setAuthentication(authentication);

                // 将userId作为请求属性传递，方便后续使用
                // 对应Go: context.WithValue(ctx, token.Identify, uid)
                request.setAttribute(JwtTokenProvider.IDENTIFY, userId);

                // 将原始Token也保存到请求属性
                // 对应Go: context.WithValue(ctx, token.Authorization, tokenStr)
                request.setAttribute(JwtTokenProvider.AUTHORIZATION, jwt);
            }
        } catch (Exception e) {
            log.error("Could not set user authentication in security context", e);
        }

        // 继续过滤器链
        filterChain.doFilter(request, response);
    }

    /**
     * 从HTTP请求中提取JWT Token
     * 对应Go: extractTokenFromHeader
     *
     * @param request HTTP请求
     * @return JWT Token字符串
     */
    private String getJwtFromRequest(HttpServletRequest request) {
        // 从Authorization头获取Token
        String bearerToken = request.getHeader(JwtTokenProvider.AUTHORIZATION);

        // 解析Bearer Token
        if (StringUtils.hasText(bearerToken)) {
            return jwtTokenProvider.resolveToken(bearerToken);
        }

        return null;
    }
}

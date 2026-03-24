/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * JWT配置属性
 * 对应Go版本: internal/config/Config.Jwt
 */
@Data
@Component
@ConfigurationProperties(prefix = "jwt")
public class JwtProperties {

    /**
     * JWT签名密钥
     * 对应Go: Config.Jwt.Secret
     */
    private String secret = "kuangbiao.camps";

    /**
     * Token过期时间（秒）
     * 对应Go: Config.Jwt.Expire
     */
    private Long expire = 8640000L; // 100天
}

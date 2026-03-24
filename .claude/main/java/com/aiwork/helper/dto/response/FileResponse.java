/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 文件上传响应
 * 对应Go版本: internal/domain/domain.go FileResp
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class FileResponse {

    /**
     * 文件访问主机地址
     */
    private String host;

    /**
     * 文件相对路径
     */
    private String file;

    /**
     * 文件名称
     */
    private String filename;
}
